# R2 Media Upload (Phase 2)

Django admin uploads media files to Cloudflare R2 and stores the public URL in the database.

## Setup

1. Create R2 API token: **R2** → **Manage R2 API Tokens** → **Create API token** (Object Read & Write).
2. Save **Access Key ID** and **Secret Access Key** (two values, not the `cfut_` Cloudflare API token).
3. Add to `.env`:

```
R2_ACCOUNT_ID=f9f326540d3d898b3aa12bf4f71f5568
R2_ACCESS_KEY_ID=your_access_key_id
R2_SECRET_ACCESS_KEY=your_secret_access_key
R2_BUCKET_NAME=quantum-edu-media
R2_PUBLIC_URL=https://pub-96a817cca5de440db5e3364bbb57f3ed.r2.dev
```

## Usage

- **Product admin:** Upload thumbnail or preview video via the "Media" section. Or paste URL.
- **Lesson admin:** Upload video, PDF, or PPT. Or paste URL.
- **Product Content admin:** When adding a Product Content with type LESSON, you can add the Lesson (including video/PDF/PPT uploads) in the same form via the "Lesson content" inline. R2 uploads work the same way.

If R2 is not configured, upload fields are hidden and the URL fields work as before.

## File Limits

| Field | Max | Types |
|-------|-----|-------|
| Thumbnail | 5 MB | JPEG, PNG, WebP, GIF |
| Preview video | 100 MB | MP4, WebM |
| Lesson video | 500 MB | MP4, WebM |
| Lesson PDF | 50 MB | PDF |
| Lesson PPT | 50 MB | PPT, PPTX |

## Object Key Structure

```
products/{product_id}/thumbnail.{ext}
products/{product_id}/preview.{ext}
lessons/{lesson_id}/video.{ext}
lessons/{lesson_id}/handout.pdf
lessons/{lesson_id}/slides.{ext}
```
