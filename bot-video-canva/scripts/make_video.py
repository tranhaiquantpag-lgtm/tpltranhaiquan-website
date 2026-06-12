#!/usr/bin/env python3
"""
make_video.py — Ghép ảnh Canva + voice-over thành MP4.

Tối ưu cho workflow Canva (ảnh đẹp sẵn):
  - Ken Burns zoom/pan trên ảnh stock thật → cinematic feel
  - Phụ đề tiếng Việt kiểu hiện đại (box style)
  - Nhạc nền tùy chọn
  - Intro/outro: dùng ảnh Canva nếu có, không thì bỏ qua

Dùng:
    python make_video.py \
        --audio 03-audio/ --images 03-images/ \
        --orientation portrait --effects on --subtitle on \
        --out 03-video.mp4
"""

from __future__ import annotations
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

SIZES = {
    "portrait":  (1080, 1920),
    "landscape": (1920, 1080),
    "square":    (1080, 1080),
}

KB_EFFECTS = ["zoom_in", "zoom_out", "pan_left", "pan_right"]


def need_ffmpeg() -> str:
    ff = shutil.which("ffmpeg")
    if ff is None:
        sys.exit("ffmpeg not found in PATH")
    return ff


# ────────────── Image handling ──────────────

def find_image(images_dir: Path, scene_id: int) -> Path | None:
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = images_dir / f"scene-{scene_id:02d}.{ext}"
        if p.exists():
            return p
    return None


def find_special_image(images_dir: Path, name: str) -> Path | None:
    """Find intro.jpg, outro.jpg etc."""
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = images_dir / f"{name}.{ext}"
        if p.exists():
            return p
    return None


def fit_image(ffmpeg: str, src: Path, size: tuple[int, int], dst: Path) -> None:
    """Crop+resize image to exact size using ffmpeg (faster than Pillow for large imgs)."""
    w, h = size
    subprocess.run([
        ffmpeg, "-y", "-i", str(src),
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,"
               f"crop={w}:{h}",
        "-q:v", "2", str(dst)
    ], check=True, capture_output=True)


# ────────────── Scene building ──────────────

def build_scene_kenburns(ffmpeg: str, image: Path, audio: Path,
                         duration: float, size: tuple[int, int],
                         out_mp4: Path, effect: str = "zoom_in") -> bool:
    """Ken Burns on a Canva image. Returns True if successful."""
    w, h = size
    frames = int(duration * 30)
    if frames < 2:
        frames = 2

    if effect == "zoom_in":
        zp = (f"zoompan=z='min(zoom+0.0008,1.15)':x='iw/2-(iw/zoom/2)':"
              f"y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps=30")
    elif effect == "zoom_out":
        zp = (f"zoompan=z='if(eq(on,1),1.15,max(zoom-0.0008,1.0))':"
              f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
              f"d={frames}:s={w}x{h}:fps=30")
    elif effect == "pan_left":
        zp = (f"zoompan=z=1.1:"
              f"x='if(eq(on,1),0,min(x+1,(iw-iw/zoom)))':y='ih/2-(ih/zoom/2)':"
              f"d={frames}:s={w}x{h}:fps=30")
    else:  # pan_right
        zp = (f"zoompan=z=1.1:"
              f"x='if(eq(on,1),(iw-iw/zoom),max(x-1,0))':y='ih/2-(ih/zoom/2)':"
              f"d={frames}:s={w}x{h}:fps=30")

    # Scale up 20% first so zoom has room
    pw, ph = int(w * 1.2), int(h * 1.2)
    vf = f"scale={pw}:{ph},{zp}"

    result = subprocess.run([
        ffmpeg, "-y",
        "-loop", "1", "-i", str(image),
        "-i", str(audio),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-t", f"{duration:.3f}", "-shortest",
        str(out_mp4),
    ], capture_output=True, text=True)

    return result.returncode == 0


def build_scene_static(ffmpeg: str, image: Path, audio: Path,
                       duration: float, size: tuple[int, int], out_mp4: Path) -> None:
    w, h = size
    subprocess.run([
        ffmpeg, "-y",
        "-loop", "1", "-i", str(image),
        "-i", str(audio),
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
               f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p",
        "-t", f"{duration:.3f}", "-r", "30",
        str(out_mp4),
    ], check=True, capture_output=True)


def build_still_clip(ffmpeg: str, image: Path, duration: float,
                     size: tuple[int, int], out_mp4: Path) -> None:
    """Image-only clip (no audio) for intro/outro."""
    w, h = size
    subprocess.run([
        ffmpeg, "-y",
        "-loop", "1", "-i", str(image),
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
               f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p",
        "-t", f"{duration:.3f}", "-r", "30",
        str(out_mp4),
    ], check=True, capture_output=True)


# ────────────── Subtitles ──────────────

def make_srt(scenes: list[dict], out_srt: Path, offset: float = 0) -> None:
    def fmt(t: float) -> str:
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t - int(t)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    cur = offset
    lines = []
    for i, s in enumerate(scenes, start=1):
        start = cur
        end = cur + s["duration_sec"]
        text = textwrap.fill(s["text"], width=36)
        lines.append(f"{i}\n{fmt(start)} --> {fmt(end)}\n{text}\n")
        cur = end + 0.5
    out_srt.write_text("\n".join(lines), encoding="utf-8")


def burn_subtitles(ffmpeg: str, video: Path, srt: Path,
                   out: Path, size: tuple[int, int]) -> None:
    w, h = size
    font_size = int(h * 0.036)
    margin_v = int(h * 0.06)
    style = (f"FontName=Arial,FontSize={font_size},"
             f"PrimaryColour=&H00FFFFFF,"
             f"OutlineColour=&H00000000,"
             f"BackColour=&H80000000,"
             f"BorderStyle=4,Outline=2,Shadow=0,"
             f"Alignment=2,"
             f"MarginV={margin_v},"
             f"MarginL={int(w*0.05)},MarginR={int(w*0.05)}")
    srt_esc = str(srt).replace("\\", "/").replace(":", r"\:")
    vf = f"subtitles='{srt_esc}':force_style='{style}'"
    subprocess.run([
        ffmpeg, "-y", "-i", str(video), "-vf", vf,
        "-c:a", "copy", "-c:v", "libx264", "-crf", "18", str(out)
    ], check=True, capture_output=True)


# ────────────── Concat + BGM ──────────────

def concat_clips(ffmpeg: str, clips: list[Path], out_mp4: Path) -> None:
    if len(clips) == 1:
        shutil.copy(clips[0], out_mp4)
        return
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{c.resolve().as_posix()}'\n")
        list_file = Path(f.name)
    try:
        subprocess.run([
            ffmpeg, "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file), "-c", "copy", str(out_mp4)
        ], check=True, capture_output=True)
    finally:
        list_file.unlink(missing_ok=True)


def add_bgm(ffmpeg: str, video: Path, bgm: Path, out: Path,
            volume: float = 0.10) -> None:
    subprocess.run([
        ffmpeg, "-y", "-i", str(video), "-stream_loop", "-1", "-i", str(bgm),
        "-filter_complex",
        f"[1:a]volume={volume},apad[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
        "-shortest", str(out),
    ], check=True, capture_output=True)


# ────────────── Main ──────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--audio", type=Path, required=True, help="Dir with scene-XX.mp3 + timing.json")
    ap.add_argument("--images", type=Path, required=True, help="Dir with scene-XX.jpg (from Canva)")
    ap.add_argument("--orientation", choices=list(SIZES), default="portrait")
    ap.add_argument("--effects", choices=["on", "off"], default="on",
                    help="Ken Burns on Canva images")
    ap.add_argument("--subtitle", choices=["on", "off"], default="on")
    ap.add_argument("--branding", choices=["on", "off"], default="off",
                    help="Use intro/outro images from 03-images/ (default: off, Canva handles it)")
    ap.add_argument("--bgm", type=Path)
    ap.add_argument("--out", type=Path, default=Path("03-video.mp4"))
    args = ap.parse_args()

    ffmpeg = need_ffmpeg()
    size = SIZES[args.orientation]

    timing_path = args.audio / "timing.json"
    if not timing_path.exists():
        sys.exit(f"Missing {timing_path}")
    timing = json.loads(timing_path.read_text(encoding="utf-8"))
    scenes = timing["scenes"]

    intro_dur = 3.0
    outro_dur = 4.0
    has_intro = False

    with tempfile.TemporaryDirectory() as tmp:
        tmpd = Path(tmp)
        clips: list[Path] = []

        # ── Intro (from Canva image if exists) ──
        intro_img = find_special_image(args.images, "intro")
        if intro_img:
            fitted = tmpd / "intro_fitted.jpg"
            fit_image(ffmpeg, intro_img, size, fitted)
            intro_clip = tmpd / "intro.mp4"
            build_still_clip(ffmpeg, fitted, intro_dur, size, intro_clip)
            clips.append(intro_clip)
            has_intro = True
            print(f"  Intro: {intro_img.name}")

        # ── Scene clips ──
        for i, s in enumerate(scenes):
            sid = s["id"]
            audio_file = args.audio / s["file"]
            if not audio_file.exists():
                sys.exit(f"Missing audio: {audio_file}")

            img = find_image(args.images, sid)
            if img is None:
                sys.exit(f"Missing image: scene-{sid:02d}.* in {args.images}/\n"
                         f"Run Canva design step first.")

            fitted = tmpd / f"scene-{sid:02d}.jpg"
            fit_image(ffmpeg, img, size, fitted)

            clip = tmpd / f"scene-{sid:02d}.mp4"
            effect = KB_EFFECTS[i % len(KB_EFFECTS)]

            if args.effects == "on":
                ok = build_scene_kenburns(ffmpeg, fitted, audio_file,
                                          s["duration_sec"], size, clip, effect)
                if not ok:
                    print(f"    Ken Burns failed scene {sid}, using static")
                    build_scene_static(ffmpeg, fitted, audio_file,
                                       s["duration_sec"], size, clip)
                    effect = "static"
            else:
                build_scene_static(ffmpeg, fitted, audio_file,
                                   s["duration_sec"], size, clip)
                effect = "static"

            clips.append(clip)
            print(f"  Scene {sid:02d} ({s.get('name', '')}): {effect}")

        # ── Outro (from Canva image if exists) ──
        outro_img = find_special_image(args.images, "outro")
        if outro_img:
            fitted = tmpd / "outro_fitted.jpg"
            fit_image(ffmpeg, outro_img, size, fitted)
            outro_clip = tmpd / "outro.mp4"
            build_still_clip(ffmpeg, fitted, outro_dur, size, outro_clip)
            clips.append(outro_clip)
            print(f"  Outro: {outro_img.name}")

        # ── Concat ──
        merged = tmpd / "merged.mp4"
        concat_clips(ffmpeg, clips, merged)
        out = merged

        # ── Subtitles ──
        if args.subtitle == "on":
            srt = tmpd / "subs.srt"
            make_srt(scenes, srt, offset=intro_dur if has_intro else 0)
            subbed = tmpd / "subbed.mp4"
            try:
                burn_subtitles(ffmpeg, out, srt, subbed, size)
                out = subbed
                print("  Subtitles: on")
            except subprocess.CalledProcessError:
                print("  Subtitles: failed (font missing?), skipping")

        # ── BGM ──
        if args.bgm and args.bgm.exists():
            with_bgm = tmpd / "with_bgm.mp4"
            add_bgm(ffmpeg, out, args.bgm, with_bgm, volume=0.10)
            out = with_bgm
            print("  BGM: on")

        args.out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(out, args.out)

    print(f"\nDone: {args.out} ({size[0]}x{size[1]})")


if __name__ == "__main__":
    main()
