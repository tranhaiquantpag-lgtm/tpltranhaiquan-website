#!/usr/bin/env python3
"""
make_voiceover.py — Sinh voice-over tiếng Việt với nhiều TTS engine.

Hỗ trợ 3 engine:
  1. ElevenLabs  — chất lượng cao nhất, giọng tự nhiên ($5+/tháng)
  2. OpenAI TTS  — chất lượng cao, cần API key
  3. edge-tts    — miễn phí, chất lượng OK (mặc định)

Dùng:
    python make_voiceover.py 02-kich-ban.md --engine edge --voice female --out 03-audio/
"""

from __future__ import annotations
import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path

try:
    from mutagen.mp3 import MP3
except ImportError:
    sys.exit("Lỗi: thiếu mutagen. Chạy: pip install mutagen --break-system-packages")


# ────────────────────── Parser kịch bản ──────────────────────

SCENE_HEADER_RE = re.compile(r"^##\s*Scene\s+(\d+)\s*[—\-:]\s*(.+?)\s*$", re.IGNORECASE)
LOI_RE = re.compile(r"^\*\*Lời:\*\*\s*(.+)$", re.IGNORECASE)


def parse_script(md_path: Path) -> list[dict]:
    scenes: list[dict] = []
    current: dict | None = None
    in_loi = False
    loi_buffer: list[str] = []

    for raw_line in md_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        m = SCENE_HEADER_RE.match(line)
        if m:
            if current is not None:
                current["text"] = " ".join(loi_buffer).strip()
                scenes.append(current)
            current = {"id": int(m.group(1)), "name": m.group(2).strip()}
            loi_buffer = []
            in_loi = False
            continue
        if current is None:
            continue
        m = LOI_RE.match(line)
        if m:
            in_loi = True
            loi_buffer.append(m.group(1).strip())
            continue
        if in_loi and line.startswith("**"):
            in_loi = False
            continue
        if in_loi and line.strip():
            loi_buffer.append(line.strip())

    if current is not None:
        current["text"] = " ".join(loi_buffer).strip()
        scenes.append(current)

    return [s for s in scenes if s.get("text")]


# ────────────────────── Chuẩn hoá text ──────────────────────

REPLACEMENTS = {
    "TPL": "Thừa phát lại",
    "THA": "thi hành án",
    "THADS": "thi hành án dân sự",
    "TPHCM": "Thành phố Hồ Chí Minh",
    "QL91": "quốc lộ chín mốt",
    "QL ": "quốc lộ ",
    "TT.": "thị trấn ",
    "VPTPL": "Văn phòng Thừa phát lại",
    "VP THADS": "Văn phòng Thi hành án dân sự",
    "NĐ-CP": "Nghị định Chính phủ",
    "THV": "Thừa hành viên",
}


def normalize_for_tts(text: str) -> str:
    for k, v in REPLACEMENTS.items():
        text = text.replace(k, v)
    text = re.sub(r"(\d{3,4})\.(\d{3})\.(\d{3,4})", r"\1 \2 \3", text)
    return text


# ────────────────────── TTS Engines ──────────────────────

class BaseTTSEngine:
    name = "base"
    def __init__(self, voice: str, rate: str):
        self.voice = voice
        self.rate = rate
    async def synthesize(self, text: str, out_path: Path) -> None:
        raise NotImplementedError


class EdgeTTSEngine(BaseTTSEngine):
    name = "edge-tts"
    VOICES = {"female": "vi-VN-HoaiMyNeural", "male": "vi-VN-NamMinhNeural"}

    def __init__(self, voice: str = "female", rate: str = "+0%"):
        actual_voice = self.VOICES.get(voice, voice)
        super().__init__(actual_voice, rate)
        try:
            import edge_tts  # noqa: F401
        except ImportError:
            sys.exit("Lỗi: thiếu edge-tts. Chạy: pip install edge-tts --break-system-packages")

    async def synthesize(self, text: str, out_path: Path) -> None:
        import edge_tts
        text = normalize_for_tts(text)
        comm = edge_tts.Communicate(text=text, voice=self.voice, rate=self.rate)
        await comm.save(str(out_path))


class ElevenLabsEngine(BaseTTSEngine):
    name = "elevenlabs"
    def __init__(self, voice: str = "female", rate: str = "+0%"):
        super().__init__(voice, rate)
        self.api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not self.api_key:
            sys.exit("Lỗi: cần ELEVENLABS_API_KEY")
        try:
            from elevenlabs.client import ElevenLabs  # noqa: F401
        except ImportError:
            sys.exit("Lỗi: thiếu elevenlabs. Chạy: pip install elevenlabs --break-system-packages")

    async def synthesize(self, text: str, out_path: Path) -> None:
        from elevenlabs.client import ElevenLabs
        text = normalize_for_tts(text)
        client = ElevenLabs(api_key=self.api_key)
        voice_id = self.voice if len(self.voice) > 10 else "21m00Tcm4TlvDq8ikWAM"
        audio_gen = client.text_to_speech.convert(
            voice_id=voice_id, text=text,
            model_id="eleven_multilingual_v2", output_format="mp3_44100_128",
        )
        with open(out_path, "wb") as f:
            for chunk in audio_gen:
                f.write(chunk)


class OpenAITTSEngine(BaseTTSEngine):
    name = "openai"
    VOICES = {"female": "nova", "male": "onyx", "warm": "shimmer"}

    def __init__(self, voice: str = "female", rate: str = "+0%"):
        actual_voice = self.VOICES.get(voice, voice)
        super().__init__(actual_voice, rate)
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            sys.exit("Lỗi: cần OPENAI_API_KEY")
        try:
            from openai import OpenAI  # noqa: F401
        except ImportError:
            sys.exit("Lỗi: thiếu openai. Chạy: pip install openai --break-system-packages")

    async def synthesize(self, text: str, out_path: Path) -> None:
        from openai import OpenAI
        text = normalize_for_tts(text)
        client = OpenAI(api_key=self.api_key)
        speed = 1.0
        rate_match = re.match(r"([+-]?\d+)%", self.rate)
        if rate_match:
            speed = 1.0 + int(rate_match.group(1)) / 100
        response = client.audio.speech.create(
            model="tts-1-hd", voice=self.voice, input=text,
            speed=max(0.25, min(4.0, speed)), response_format="mp3",
        )
        response.stream_to_file(str(out_path))


ENGINE_MAP = {"edge": EdgeTTSEngine, "elevenlabs": ElevenLabsEngine, "openai": OpenAITTSEngine}


# ────────────────────── Audio utils ──────────────────────

def get_duration_sec(mp3_path: Path) -> float:
    return float(MP3(mp3_path).info.length)


def concat_mp3(paths: list[Path], out_path: Path, gap_ms: int = 500) -> None:
    import shutil, subprocess, tempfile
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        with out_path.open("wb") as fout:
            for p in paths:
                fout.write(p.read_bytes())
        return

    with tempfile.TemporaryDirectory() as tmp:
        silence = Path(tmp) / "silence.mp3"
        subprocess.run(
            [ffmpeg, "-y", "-f", "lavfi", "-i",
             f"anullsrc=r=24000:cl=mono", "-t", f"{gap_ms/1000:.3f}",
             "-q:a", "9", "-acodec", "libmp3lame", str(silence)],
            check=True, capture_output=True,
        )
        list_file = Path(tmp) / "list.txt"
        lines = []
        for i, p in enumerate(paths):
            lines.append(f"file '{p.resolve().as_posix()}'")
            if i < len(paths) - 1:
                lines.append(f"file '{silence.resolve().as_posix()}'")
        list_file.write_text("\n".join(lines), encoding="utf-8")
        subprocess.run(
            [ffmpeg, "-y", "-f", "concat", "-safe", "0",
             "-i", str(list_file), "-c", "copy", str(out_path)],
            check=True, capture_output=True,
        )


# ────────────────────── Main ──────────────────────

async def main_async() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", type=Path)
    ap.add_argument("--engine", choices=list(ENGINE_MAP), default="edge")
    ap.add_argument("--voice", default="female")
    ap.add_argument("--rate", default="+0%")
    ap.add_argument("--out", type=Path, default=Path("03-audio"))
    args = ap.parse_args()

    if not args.script.exists():
        sys.exit(f"Không tìm thấy: {args.script}")

    args.out.mkdir(parents=True, exist_ok=True)
    engine = ENGINE_MAP[args.engine](voice=args.voice, rate=args.rate)
    print(f"Engine: {engine.name} | Voice: {engine.voice} | Rate: {args.rate}")

    scenes = parse_script(args.script)
    if not scenes:
        sys.exit("Không parse được scene nào.")

    print(f"{len(scenes)} scene")
    timing: list[dict] = []
    mp3_paths: list[Path] = []

    for s in scenes:
        sid = s["id"]
        out_path = args.out / f"scene-{sid:02d}.mp3"
        print(f"  Scene {sid:02d} ({s['name']}): {len(s['text'])} chars ... ", end="", flush=True)
        await engine.synthesize(s["text"], out_path)
        dur = get_duration_sec(out_path)
        print(f"{dur:.1f}s")
        timing.append({
            "id": sid, "name": s["name"], "duration_sec": round(dur, 3),
            "file": out_path.name, "text": s["text"],
        })
        mp3_paths.append(out_path)

    full_path = args.out / "full.mp3"
    concat_mp3(mp3_paths, full_path, gap_ms=500)
    full_dur = get_duration_sec(full_path)

    timing_meta = {
        "engine": engine.name, "voice": engine.voice, "rate": args.rate,
        "total_duration_sec": round(full_dur, 3), "scenes": timing,
    }
    (args.out / "timing.json").write_text(
        json.dumps(timing_meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nXong — {full_dur:.1f}s | {args.out / 'timing.json'}")


def main() -> None:
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
