# olmOCR API (minimal)

FastAPI service for OCR using `allenai/olmOCR-2-7B-1025-FP8`.

## Build and Run (Docker)

```bash
# build
docker build -t alexxyk/olmocr-api:latest .

# run (GPU)
docker run --gpus all -p 5005:5005 alexxyk/olmocr-api:latest
```

## Endpoints

- GET `/` — service info
- GET `/health` — health check
- GET `/metrics` — minimal runtime metrics
- POST `/ocr` — multipart form: `file=@image.jpg`
  - Optional query param: `convert_html_tables=true` to convert HTML tables to Markdown via pandoc with `-tex_math_dollars`.
  - PDF support: send `file=@doc.pdf`. Optional query params:
    - `pdf_dpi` (default 200)
    - `max_pages` (default all)
    - `page_separator` (default `---`) used between pages

Example:
```bash
curl -X POST -F "file=@image.jpg" "http://localhost:5005/ocr?convert_html_tables=true"
```

PDF example:
```bash
curl -X POST -F "file=@doc.pdf" "http://localhost:5005/ocr?pdf_dpi=200&max_pages=5&page_separator=---"
```

## Notes
- Requires NVIDIA GPU (recommended) and CUDA-compatible drivers for best performance.
- Env vars: `MODEL_NAME`, `PROCESSOR_NAME`, `TARGET_IMAGE_DIM`, `PORT`.
