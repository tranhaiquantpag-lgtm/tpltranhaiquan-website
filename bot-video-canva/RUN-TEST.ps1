# ============================================================
# BOT VIDEO CANVA — Download 7 anh Canva + xem thu
# Chay: Right-click > Run with PowerShell
# ============================================================

$ErrorActionPreference = "Stop"
$dest = "$env:USERPROFILE\Desktop\canva-video-test\03-images"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

Write-Host "=== DOWNLOADING 7 CANVA DESIGNS ===" -ForegroundColor Cyan

$images = @(
    @{name="intro.jpg";    url="https://export-download.canva.com/PlKoo/DAHL-BPlKoo/-1/0/0001-1482190024449786081.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAQYCGKMUH5AO7UJ26%2F20260608%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260608T022735Z&X-Amz-Expires=29675&X-Amz-Signature=0c963011ae300cea159e37ba4cd60756720b7a639421540779bd33e7d042d25c&X-Amz-SignedHeaders=host%3Bx-amz-expected-bucket-owner&response-expires=Mon%2C%2008%20Jun%202026%2010%3A42%3A10%20GMT"},
    @{name="scene-01.jpg"; url="https://export-download.canva.com/PlKoo/DAHL-BPlKoo/-1/0/0002-1482190024449786081.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAQYCGKMUH5AO7UJ26%2F20260608%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260608T011158Z&X-Amz-Expires=32944&X-Amz-Signature=bdffe6958c5c7d041239e8703bfab15308e82f18798b09ab8d9b718ad0e22a43&X-Amz-SignedHeaders=host%3Bx-amz-expected-bucket-owner&response-expires=Mon%2C%2008%20Jun%202026%2010%3A21%3A02%20GMT"},
    @{name="scene-02.jpg"; url="https://export-download.canva.com/PlKoo/DAHL-BPlKoo/-1/0/0003-1482190024449786081.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAQYCGKMUH5AO7UJ26%2F20260608%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260608T032607Z&X-Amz-Expires=27350&X-Amz-Signature=73b6b0def9ee72f7f458f22ace9d9264d36fc7b2f06c9ecf66daaa951700f716&X-Amz-SignedHeaders=host%3Bx-amz-expected-bucket-owner&response-expires=Mon%2C%2008%20Jun%202026%2011%3A01%3A57%20GMT"},
    @{name="scene-03.jpg"; url="https://export-download.canva.com/PlKoo/DAHL-BPlKoo/-1/0/0004-1482190024449786081.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAQYCGKMUH5AO7UJ26%2F20260608%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260608T084705Z&X-Amz-Expires=8284&X-Amz-Signature=65e9615c785b371776b0b9f0363899bfc08cb9e3a41a8545fbaebb0ac6e8aa8b&X-Amz-SignedHeaders=host%3Bx-amz-expected-bucket-owner&response-expires=Mon%2C%2008%20Jun%202026%2011%3A05%3A09%20GMT"},
    @{name="scene-04.jpg"; url="https://export-download.canva.com/PlKoo/DAHL-BPlKoo/-1/0/0005-1482190024449786081.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAQYCGKMUH5AO7UJ26%2F20260607%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260607T201415Z&X-Amz-Expires=51794&X-Amz-Signature=7cd5ac9983068f4126510b8c5f47a8ceee7e1a524728509ba6404af3874423f2&X-Amz-SignedHeaders=host%3Bx-amz-expected-bucket-owner&response-expires=Mon%2C%2008%20Jun%202026%2010%3A37%3A29%20GMT"},
    @{name="scene-05.jpg"; url="https://export-download.canva.com/PlKoo/DAHL-BPlKoo/-1/0/0006-1482190024449786081.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAQYCGKMUH5AO7UJ26%2F20260608%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260608T022049Z&X-Amz-Expires=28343&X-Amz-Signature=5a13360c39077b0951b29d09f0691eac4851a00beb90af435153533985f8e646&X-Amz-SignedHeaders=host%3Bx-amz-expected-bucket-owner&response-expires=Mon%2C%2008%20Jun%202026%2010%3A13%3A12%20GMT"},
    @{name="outro.jpg";    url="https://export-download.canva.com/PlKoo/DAHL-BPlKoo/-1/0/0007-1482190024449786081.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAQYCGKMUH5AO7UJ26%2F20260608%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260608T024749Z&X-Amz-Expires=26644&X-Amz-Signature=99962d8c21b914849403fadf9fb1f9d69cce6cd2daf6c6014f2f55971b7f0c08&X-Amz-SignedHeaders=host%3Bx-amz-expected-bucket-owner&response-expires=Mon%2C%2008%20Jun%202026%2010%3A11%3A53%20GMT"}
)

$wc = New-Object System.Net.WebClient
foreach ($img in $images) {
    $file = "$dest\$($img.name)"
    Write-Host "  $($img.name) ... " -NoNewline
    try {
        $wc.DownloadFile($img.url, $file)
        $sz = [math]::Round((Get-Item $file).Length / 1KB)
        Write-Host "${sz} KB OK" -ForegroundColor Green
    } catch {
        Write-Host "FAILED" -ForegroundColor Red
    }
}
$wc.Dispose()

# Mo thu muc de xem
Write-Host "`nMo thu muc anh..." -ForegroundColor Cyan
Start-Process explorer.exe $dest

Write-Host "`n=== XONG ===" -ForegroundColor Green
Write-Host "7 anh Canva da luu tai: $dest"
Write-Host "URLs het han sau ~2 gio, chay nhanh!"

Read-Host "`nNhan Enter de dong"
