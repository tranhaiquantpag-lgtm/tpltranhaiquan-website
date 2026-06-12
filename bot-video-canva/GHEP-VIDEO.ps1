# ============================================================
# GHEP VIDEO TU ANH CANVA — Chay sau khi da download anh
# Right-click > Run with PowerShell
# ============================================================

$ErrorActionPreference = "Continue"
$project = "$env:USERPROFILE\Desktop\canva-video-test"
$images  = "$project\03-images"
$audio   = "$project\03-audio"
$scripts = "$env:USERPROFILE\OneDrive\Máy tính\Tài liệu\Documents\GitHub\tpltranhaiquan-website\bot-video-canva\scripts"

Write-Host "=== GHEP VIDEO VI BANG NHA DAT ===" -ForegroundColor Cyan

# Kiem tra anh
$imgCount = (Get-ChildItem "$images\*.jpg" -ErrorAction SilentlyContinue).Count
if ($imgCount -lt 5) {
    Write-Host "LOI: Chi co $imgCount anh. Chay RUN-TEST.ps1 truoc!" -ForegroundColor Red
    Read-Host "Nhan Enter de dong"
    exit 1
}
Write-Host "  $imgCount anh Canva OK" -ForegroundColor Green

# Kiem tra ffmpeg
$ff = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ff) {
    Write-Host "LOI: Chua cai ffmpeg. Chay: winget install ffmpeg" -ForegroundColor Red
    Read-Host "Nhan Enter de dong"
    exit 1
}
Write-Host "  ffmpeg OK" -ForegroundColor Green

# Kiem tra Python
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "LOI: Chua cai Python." -ForegroundColor Red
    Read-Host "Nhan Enter de dong"
    exit 1
}
Write-Host "  python OK" -ForegroundColor Green

# ---- BUOC 1: Cai packages ----
Write-Host "`n[1/3] Cai packages..." -ForegroundColor Yellow
pip install edge-tts mutagen --quiet 2>$null
Write-Host "  edge-tts + mutagen OK" -ForegroundColor Green

# ---- BUOC 2: Voice-over ----
Write-Host "`n[2/3] Tao voice-over (edge-tts)..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $audio | Out-Null

# Tao kich ban
$scriptMd = @"
# Lap Vi Bang Mua Ban Nha Dat

## Scene 1 — Hook (5s)
**Hinh:** cap vo chong lo lang
**Text tren hinh:** Mua nha so bi lua?
**Loi:** Bạn đang chuẩn bị mua bán nhà đất mà lo sợ rủi ro?

## Scene 2 — Van de (8s)
**Hinh:** tranh chap
**Text tren hinh:** Tranh chap xay ra moi ngay
**Loi:** Mỗi năm có hàng ngàn vụ tranh chấp nhà đất vì không có bằng chứng giao dịch rõ ràng.

## Scene 3 — Giai phap (10s)
**Hinh:** thua phat lai
**Text tren hinh:** Vi bang — bang chung phap ly
**Loi:** Vi bằng do Thừa phát lại lập là bằng chứng hợp pháp, được Tòa án công nhận, giúp bảo vệ quyền lợi của bạn.

## Scene 4 — Quy trinh (12s)
**Hinh:** infographic
**Text tren hinh:** 3 buoc don gian
**Loi:** Chỉ cần 3 bước. Một là liên hệ Văn phòng. Hai là Thừa phát lại đến tận nơi ghi nhận sự kiện. Ba là bạn nhận vi bằng có giá trị pháp lý.

## Scene 5 — CTA (8s)
**Hinh:** van phong
**Text tren hinh:** Lien he ngay
**Loi:** Liên hệ Văn phòng Thừa phát lại An Giang qua hotline 0968 181 169 để được tư vấn miễn phí.
"@
$scriptMd | Out-File -Encoding UTF8 "$project\02-kich-ban.md"

python "$scripts\make_voiceover.py" "$project\02-kich-ban.md" --engine edge --voice female --out "$audio"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Voice FAILED!" -ForegroundColor Red
    Write-Host "  Thu chay: pip install edge-tts mutagen" -ForegroundColor Yellow
    Read-Host "Nhan Enter de dong"
    exit 1
}
Write-Host "  Voice OK" -ForegroundColor Green

# ---- BUOC 3: Ghep video ----
Write-Host "`n[3/3] Ghep video..." -ForegroundColor Yellow
$outVideo = "$project\video-vi-bang-nha-dat.mp4"

python "$scripts\make_video.py" `
    --audio "$audio" `
    --images "$images" `
    --orientation portrait `
    --effects off `
    --subtitle on `
    --out "$outVideo"

if ($LASTEXITCODE -ne 0) {
    Write-Host "  Video FAILED!" -ForegroundColor Red
    Read-Host "Nhan Enter de dong"
    exit 1
}

# ---- KET QUA ----
Write-Host "`n=== HOAN THANH ===" -ForegroundColor Green
$sz = [math]::Round((Get-Item $outVideo).Length / 1MB, 1)
Write-Host "Video: $outVideo ($sz MB)" -ForegroundColor Cyan
Write-Host "1080x1920 (Short/Reels)" -ForegroundColor Cyan
Write-Host "Hinh: 7 Canva AI designs" -ForegroundColor Cyan
Write-Host "Voice: Edge-TTS (vi-VN-HoaiMyNeural)" -ForegroundColor Cyan

# Mo video
Start-Process $outVideo

Read-Host "`nNhan Enter de dong"
