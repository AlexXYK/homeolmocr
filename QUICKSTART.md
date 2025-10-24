# Quick Start Guide

Get your olmOCR API up and running in minutes!

## Prerequisites

- Docker with NVIDIA Container Toolkit
- NVIDIA GPU with 16GB+ VRAM
- Docker Hub account (for deployment)

## 1. Quick Test (30 seconds)

Verify everything is set up correctly:

```bash
python check_setup.py
```

You should see all checks pass ✅

## 2. Build Docker Image (5-10 minutes)

```bash
# Build the image
docker build -t yourusername/olmocr-api:latest .

# This will:
# - Set up CUDA environment
# - Install Python dependencies
# - Configure the API service
```

## 3. Test Locally (First run: 10-15 minutes)

```bash
# Start the container
docker run --gpus all -p 5005:5005 yourusername/olmocr-api:latest

# The first run will download the model (~14GB)
# Subsequent runs are instant
```

Wait for the message: `Model and processor loaded successfully!`

## 4. Test the API

In a new terminal:

```bash
# Health check
curl http://localhost:5005/health

# Process an image
curl -X POST -F "file=@path/to/image.jpg" http://localhost:5005/ocr
```

Or use the test script:

```bash
python test_api.py "C:\Users\alexa\OneDrive\Pictures\grandmatest.jpg"
```

## 5. Push to Docker Hub (2 minutes)

```bash
# Login
docker login

# Push
docker push yourusername/olmocr-api:latest
```

Or use the automated script:

```bash
# Windows (PowerShell)
.\build_and_push.sh

# Linux/Mac
chmod +x build_and_push.sh
./build_and_push.sh
```

## 6. Deploy with Portainer

### Option A: Using Portainer UI

1. Open Portainer web interface
2. Go to **Stacks** → **Add Stack**
3. Name it `olmocr-api`
4. Paste this configuration:

```yaml
version: '3.8'

services:
  olmocr-api:
    image: yourusername/olmocr-api:latest
    container_name: olmocr-api
    ports:
      - "5005:5005"
    environment:
      - PORT=5005
      - MODEL_NAME=allenai/olmOCR-2-7B-1025-FP8
      - PROCESSOR_NAME=Qwen/Qwen2.5-VL-7B-Instruct
      - TARGET_IMAGE_DIM=1288
    volumes:
      - huggingface_cache:/root/.cache/huggingface
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

volumes:
  huggingface_cache:
    driver: local
```

5. Click **Deploy the stack**

### Option B: Using docker-compose

```bash
# Update docker-compose.yml with your Docker Hub username
# Then:
docker-compose up -d
```

## 7. Use from Your Phone

### iOS Shortcuts

1. Open **Shortcuts** app
2. Create new shortcut
3. Add actions:
   - Select Photos
   - Get Contents of URL
     - URL: `http://your-server-ip:5005/ocr`
     - Method: POST
     - Request Body: Form
     - Add field: `file` = Photo
4. Save and run

### Android HTTP Shortcuts

1. Install **HTTP Shortcuts** app
2. Create new shortcut
3. Configure:
   - URL: `http://your-server-ip:5005/ocr`
   - Method: POST
   - Body type: Multipart
   - Add file parameter: `file`
4. Select image source

### Using curl from anywhere

```bash
curl -X POST \
  -F "file=@image.jpg" \
  http://your-server-ip:5005/ocr
```

## API Response Format

```json
{
  "success": true,
  "text": "# Extracted Text\n\nYour document content in markdown...",
  "metadata": {
    "original_size": [2000, 3000],
    "processed_size": [859, 1288],
    "filename": "image.jpg",
    "model": "allenai/olmOCR-2-7B-1025-FP8"
  }
}
```

## Troubleshooting

### Container exits immediately

```bash
# Check logs
docker logs olmocr-api

# Common fix: Ensure GPU is available
nvidia-smi
```

### Out of memory

```bash
# Reduce image processing size
docker run -e TARGET_IMAGE_DIM=800 ...
```

### Model download fails

```bash
# Manually download model
docker exec -it olmocr-api bash
huggingface-cli download allenai/olmOCR-2-7B-1025-FP8
```

### API timeout

The first request takes longer (model warmup). Subsequent requests are fast.

## Performance Tips

1. **First Request**: 30-60 seconds (model loading)
2. **Subsequent Requests**: 2-5 seconds per image
3. **Optimal Image Size**: 1288px longest dimension
4. **Batch Processing**: Process images sequentially to avoid OOM

## Security Recommendations

For production use:

```python
# Add to app.py
from fastapi import Header, HTTPException

API_KEY = os.getenv("API_KEY", "your-secret-key")

@app.post("/ocr", dependencies=[Depends(verify_api_key)])
async def process_ocr(...):
    # Your endpoint code
```

Then add to docker-compose.yml:
```yaml
environment:
  - API_KEY=your-secure-random-key
```

## Next Steps

- Read [README.md](README.md) for complete documentation
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for advanced deployment options
- Review [CONTRIBUTING.md](CONTRIBUTING.md) if you want to contribute

## Support

- GitHub Issues: [Report a problem]
- Model Info: https://huggingface.co/allenai/olmOCR-2-7B-1025-FP8
- Original Project: https://github.com/allenai/olmocr

---

**Ready to process millions of documents? Start now!** 🚀

