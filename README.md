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

Example:
```bash
curl -X POST -F "file=@image.jpg" "http://localhost:5005/ocr?convert_html_tables=true"
```

## Notes
- Requires NVIDIA GPU (recommended) and CUDA-compatible drivers for best performance.
- Env vars: `MODEL_NAME`, `PROCESSOR_NAME`, `TARGET_IMAGE_DIM`, `PORT`.
