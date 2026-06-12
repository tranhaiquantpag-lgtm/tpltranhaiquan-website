---
name: bot-video-canva
description: "Bot sản xuất video pháp lý bằng Canva AI — hình ảnh thật, thiết kế chuyên nghiệp. Kích hoạt khi người dùng nói: làm video đẹp, video canva, tạo video mới, video thừa phát lại, video vi bằng, video thi hành án, hoặc muốn video có hình ảnh đẹp/thật hơn. Bot dùng Canva MCP tạo design cho từng scene → export ảnh → ghép với voice-over → ra MP4 sẵn sàng đăng."
---

# Bot Video Canva — Văn phòng Thừa phát lại An Giang

Bot này dùng **Canva AI** để tạo hình ảnh chuyên nghiệp cho video, khác hoàn toàn với bot cũ (Pillow/Python). Kết quả: video có hình stock thật, thiết kế đẹp như agency.

## Thông tin văn phòng (KHÔNG ĐƯỢC THAY ĐỔI)

- **Tên:** Văn phòng Thừa phát lại An Giang
- **Đại diện:** Thừa phát lại Trần Hải Quân
- **Hotline:** 0968.181.169 — 0945.432.333
- **Địa chỉ:** 202 Lê Lợi (QL91), ấp Hòa Phú 4, TT. An Châu, Châu Thành, An Giang
- **Web:** tpltranhaiquan.online
- **Facebook:** facebook.com/tranhaiquanag
- **YouTube:** youtube.com/@Thquanag
- **Email:** tranhaiquantpag@gmail.com

## Pipeline 5 bước

```
[1] BRIEF → [2] KỊCH BẢN → [3] CANVA DESIGN → [4] VOICE + VIDEO → [5] CAPTION + BUNDLE
```

---

### Bước 1 — Brief

Hỏi người dùng tối đa 2 câu (nếu chưa rõ):
1. Chủ đề cụ thể? (lập vi bằng / xác minh THA / tổ chức THA / tống đạt / tư vấn / khác)
2. Short (≤60s, dọc 9:16) hay Long (2-4 phút, ngang 16:9)?

Mặc định: Short, khán giả người dân.

### Bước 2 — Kịch bản

Viết kịch bản theo format:

```markdown
## Scene 1 — Hook (5s)
**Hình:** [Mô tả hình ảnh chi tiết để Canva AI hiểu — VD: "Cảnh một gia đình trẻ đang ký hợp đồng mua nhà, bàn tay cầm bút, giấy tờ trên bàn, tone ấm"]
**Text trên hình:** [Dòng chữ ngắn hiển thị trên slide — VD: "Bạn đang mua nhà?"]
**Lời:** [Voice-over script — VD: "Bạn đang chuẩn bị mua bán nhà đất?"]

## Scene 2 — Vấn đề (8s)
**Hình:** [Mô tả chi tiết]
**Text trên hình:** [Chữ trên slide]
**Lời:** [Voice-over]
...
```

Nguyên tắc:
- Câu ngắn ≤14 từ, đọc tự nhiên
- Hook nói VẤN ĐỀ khách hàng, không nói về VP
- KHÔNG tư vấn pháp luật cụ thể
- KHÔNG hứa kết quả
- Mô tả hình ảnh phải CHI TIẾT để Canva AI tạo đúng (tone màu, bối cảnh, đối tượng)

Lưu kịch bản vào `02-kich-ban.md`.

### Bước 3 — Canva Design (PHẦN QUAN TRỌNG NHẤT)

Với MỖI scene trong kịch bản, gọi Canva MCP để tạo design:

#### 3a. Chọn design_type phù hợp:
- **Short (9:16):** dùng `your_story` (1080×1920)
- **Long (16:9):** dùng `facebook_post` hoặc `youtube_thumbnail`

#### 3b. Gọi `generate-design` cho từng scene:

```
Tool: mcp__canva__generate-design
Params:
  design_type: "your_story"  (hoặc loại phù hợp)
  query: "[Mô tả chi tiết từ **Hình:** trong kịch bản]. Professional legal services design. 
          Text overlay: '[Text trên hình]'. 
          Color scheme: navy blue (#0C2344), gold accent (#DAA520), white text.
          Footer: 'VP Thừa phát lại An Giang | 0968.181.169'.
          Style: professional, trustworthy, modern Vietnamese legal firm."
  user_intent: "Creating scene X slide for legal services video"
```

#### 3c. Chọn candidate tốt nhất:
- `generate-design` trả về nhiều candidates (preview URLs)
- Chọn candidate phù hợp nhất
- Gọi `create-design-from-candidate` để lưu thành design

#### 3d. Export ảnh:
```
Tool: mcp__canva__export-design
Params:
  design_id: "D..."
  format: { type: "jpg", quality: 95, width: 1080, height: 1920 }
```

#### 3e. Tải ảnh về workspace:
- Dùng URL export để download ảnh vào `03-images/scene-XX.jpg`

#### 3f. Làm tương tự cho INTRO và OUTRO:

**Intro query mẫu:**
```
"Professional legal firm video intro. Large title: '[Tiêu đề video]'. 
Subtitle: 'Thừa phát lại Trần Hải Quân'. 
Bottom: 'Hotline: 0968.181.169 — 0945.432.333'.
Navy blue gradient background, gold accents, scales of justice icon, 
elegant and trustworthy Vietnamese law firm branding."
```

**Outro query mẫu:**
```
"Contact us / Call to action slide for Vietnamese legal firm.
Large text: 'LIÊN HỆ NGAY'. 
Info: Hotline 0968.181.169 — 0945.432.333, 
202 Lê Lợi, An Châu, An Giang, tpltranhaiquan.online.
Professional, navy blue, gold accents.
Bottom CTA: Like · Subscribe · Share."
```

### Bước 4 — Voice-over + Ghép Video

#### 4a. Voice-over
Chạy script `make_voiceover.py` (trong thư mục scripts/):

```bash
python scripts/make_voiceover.py 02-kich-ban.md --engine edge --voice female --out 03-audio/
```

Hoặc engine tốt hơn nếu có API key:
```bash
python scripts/make_voiceover.py 02-kich-ban.md --engine elevenlabs --out 03-audio/
```

#### 4b. Ghép video
Chạy script `make_video.py`:

```bash
python scripts/make_video.py \
    --audio 03-audio/ \
    --images 03-images/ \
    --orientation portrait \
    --effects on \
    --subtitle on \
    --branding off \
    --out 03-video.mp4
```

**LƯU Ý:** `--branding off` vì intro/outro đã do Canva tạo (đẹp hơn tự sinh).
`--effects on` để có Ken Burns zoom/pan trên ảnh Canva.

### Bước 5 — Caption + Bundle

Gọi skill `viet-bai-dang-tpl` để viết caption cho 3 nền tảng (Web, Facebook, YouTube).

Gom tất cả vào thư mục `05-bundle/`:
- `video.mp4`
- `thumbnail.jpg` (export từ Canva — scene đẹp nhất)
- `caption-web.md`, `caption-fb.md`, `caption-yt.md`
- `README-dang-bai.md`

---

## Khi Canva MCP không khả dụng (FALLBACK)

Nếu Canva MCP không kết nối hoặc lỗi:
1. Thông báo cho người dùng: "Canva chưa kết nối, dùng auto-slides thay thế"
2. Chạy `make_video.py` với `--auto-slides --branding on`
3. Kết quả sẽ kém đẹp hơn nhưng vẫn hoạt động

---

## Ví dụ chạy đầy đủ

**Người dùng:** "Làm video ngắn về lập vi bằng giao tiền đặt cọc nhà đất"

**Bot thực hiện:**

1. **Brief:** Short 60s, khán giả người dân, chủ đề vi bằng đặt cọc — đủ rõ, không cần hỏi thêm.

2. **Kịch bản:** 5 scene (hook → vấn đề → giải pháp → quy trình → CTA), lưu `02-kich-ban.md`.

3. **Canva Design:** 
   - Gọi `generate-design` type `your_story` cho 7 slides (intro + 5 scene + outro)
   - Mỗi slide có mô tả chi tiết: "Young couple signing house deposit contract, Vietnamese setting, worried expression, money on table..."
   - Chọn best candidate → `create-design-from-candidate` → `export-design` JPG
   - Download 7 ảnh vào `03-images/`

4. **Voice + Video:**
   - `make_voiceover.py` → 5 file MP3 + timing.json
   - `make_video.py` → MP4 1080×1920, Ken Burns, phụ đề tiếng Việt

5. **Caption:** Gọi `viet-bai-dang-tpl` → 3 bài Web/FB/YT

6. **Trả kết quả:**
```
✅ Video đã sẵn sàng

📁 Bundle: outputs/video-vi-bang-dat-coc-20260608/05-bundle/
🎬 video.mp4 — 55s, 1080×1920 (Short)
🖼 Hình ảnh: Canva AI (7 slides thiết kế chuyên nghiệp)
🎙 Voice: Edge-TTS (vi-VN-HoaiMyNeural)
📝 Caption: Web · Facebook · YouTube

Bạn muốn:
  1) Xem từng slide Canva trước khi ghép
  2) Đổi voice sang ElevenLabs (tự nhiên hơn)
  3) Upload luôn lên Facebook/Web
```

---

## Nguyên tắc TUYỆT ĐỐI

1. **KHÔNG sai thông tin liên hệ** — số điện thoại, địa chỉ, website phải đúng 100%
2. **KHÔNG tự đăng bài** lên Facebook/Web khi chưa có xác nhận + token
3. **KHÔNG tư vấn pháp luật** trong kịch bản — chỉ giới thiệu dịch vụ
4. **KHÔNG hứa kết quả** pháp lý
5. **Mỗi bước lưu file** — để người dùng review được
6. **Ưu tiên Canva** — chỉ fallback về auto-slides khi Canva không khả dụng
7. **Hỏi người dùng chọn candidate** Canva nếu có nhiều lựa chọn, trừ khi đang chạy tự động (scheduled task)

## Scripts đi kèm

- `scripts/make_voiceover.py` — TTS đa engine (edge/elevenlabs/openai)
- `scripts/make_video.py` — Ghép ảnh + audio + subtitle + effects
- `scripts/post_bundle.py` — Gom bundle
- `scripts/post_facebook.py` — Đăng FB (cần token)
- `scripts/post_wordpress.py` — Đăng WP (cần App Password)
