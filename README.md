# olmOCR API Service

A production-ready REST API for OCR processing using the olmOCR-2-7B-1025-FP8 model from Allen AI. This service converts images and documents to markdown format with high accuracy.

## 🚀 Features

- **High-Accuracy OCR**: Uses the state-of-the-art olmOCR-2-7B-1025-FP8 model
- **Markdown Output**: Extracts text in clean markdown format preserving structure
- **REST API**: Easy-to-use FastAPI endpoint for integration
- **Docker Support**: Fully containerized with GPU support
- **Portainer Compatible**: Ready-to-use docker-compose stack
- **Production Ready**: Health checks, error handling, and logging

## 📋 Prerequisites

- **GPU**: NVIDIA GPU with at least 16GB VRAM (recommended)
- **CUDA**: CUDA 12.1 or compatible
- **Docker**: Docker Engine with NVIDIA Container Toolkit
- **Docker Compose**: For orchestration (optional)

## 🏗️ Architecture

```
├── app.py                 # Main FastAPI application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container definition
├── docker-compose.yml    # Portainer stack configuration
├── entrypoint.sh         # Container startup script
├── test_api.py           # Testing script
└── README.md             # This file
```

## 🐳 Docker Hub Setup

### 1. Build the Docker Image

```bash
# Build the image
docker build -t yourusername/olmocr-api:latest .

# Test locally first
docker run --gpus all -p 5005:5005 yourusername/olmocr-api:latest
```

### 2. Push to Docker Hub

```bash
# Login to Docker Hub
docker login

# Push the image
docker push yourusername/olmocr-api:latest
```

### 3. Deploy with Portainer

1. Log into your Portainer instance
2. Navigate to **Stacks** → **Add Stack**
3. Name it `olmocr-api`
4. Paste the contents of `docker-compose.yml`
5. Update the `DOCKER_USERNAME` environment variable
6. Deploy the stack

## 📦 Portainer Stack Configuration

The `docker-compose.yml` is optimized for Portainer deployment:

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
```

## 🔧 Local Development

### Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd olmocr-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the API
python app.py
```

### Testing

```bash
# Test with an image
python test_api.py path/to/your/image.jpg

# Test with custom API URL
python test_api.py path/to/your/image.jpg http://localhost:5005
```

## 📡 API Reference

### Base URL
```
http://your-server-ip:5005
```

### Endpoints

#### 1. Root Endpoint
**GET** `/`

Returns API information and available endpoints.

**Example:**
```bash
curl http://localhost:5005/
```

**Response:**
```json
{
  "service": "olmOCR API",
  "version": "1.0.0",
  "model": "allenai/olmOCR-2-7B-1025-FP8",
  "status": "ready",
  "device": "cuda:0",
  "endpoints": {
    "health": "/health",
    "ocr": "/ocr (POST with image file)"
  }
}
```

---

#### 2. Health Check
**GET** `/health`

Check if the API is running and the model is loaded.

**Example:**
```bash
curl http://localhost:5005/health
```

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cuda:0",
  "cuda_available": true
}
```

**Status Codes:**
- `200 OK`: Service is healthy
- `503 Service Unavailable`: Model not loaded yet

---

#### 3. OCR Processing
**POST** `/ocr`

Extract text from an image and return it in markdown format.

**Content-Type:** `multipart/form-data`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | Image file (JPEG, PNG, GIF, WebP, etc.) |

**Example (curl):**
```bash
curl -X POST \
  -F "file=@/path/to/image.jpg" \
  http://localhost:5005/ocr
```

**Example (curl with headers):**
```bash
curl -X POST \
  -H "Accept: application/json" \
  -F "file=@/path/to/image.jpg" \
  http://localhost:5005/ocr
```

**Example (Tasker/HTTP Request):**
```
URL: http://your-server-ip:5005/ocr
Method: POST
Content-Type: multipart/form-data
Body:
  - Field name: file
  - Field type: File
  - File source: Camera/Gallery/File
```

**Example (Python):**
```python
import requests

with open('image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5005/ocr',
        files={'file': ('image.jpg', f, 'image/jpeg')}
    )
    result = response.json()
    print(result['text'])
```

**Example (JavaScript):**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:5005/ocr', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data.text));
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "text": "# Heading\n\nExtracted text in markdown format...",
  "error": null,
  "metadata": {
    "original_size": [2000, 3000],
    "processed_size": [859, 1288],
    "filename": "image.jpg",
    "model": "allenai/olmOCR-2-7B-1025-FP8"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "text": null,
  "error": "Invalid image file: cannot identify image file",
  "metadata": null
}
```

**Error Response (503 Service Unavailable):**
```json
{
  "detail": "Model not loaded yet"
}
```

**Status Codes:**
- `200 OK`: Image processed successfully
- `400 Bad Request`: Invalid image or missing file
- `422 Unprocessable Entity`: Missing required parameter
- `503 Service Unavailable`: Model not ready
- `500 Internal Server Error`: Processing error

---

### Complete curl Examples

**Basic OCR request:**
```bash
curl -X POST -F "file=@image.jpg" http://localhost:5005/ocr
```

**With timeout (5 minutes):**
```bash
curl --max-time 300 -X POST -F "file=@image.jpg" http://localhost:5005/ocr
```

**Save response to file:**
```bash
curl -X POST -F "file=@image.jpg" http://localhost:5005/ocr | jq -r '.text' > output.md
```

**With error handling:**
```bash
curl -X POST -F "file=@image.jpg" http://localhost:5005/ocr \
  && echo "Success" || echo "Failed"
```

**From URL (download first):**
```bash
# Download image
curl -o temp.jpg https://example.com/image.jpg

# Process it
curl -X POST -F "file=@temp.jpg" http://localhost:5005/ocr
```

---

### Response Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `success` | Boolean | `true` if OCR succeeded, `false` if error occurred |
| `text` | String or null | Extracted text in markdown format (null if error) |
| `error` | String or null | Error message if processing failed (null if success) |
| `metadata` | Object or null | Additional information about the processing |
| `metadata.original_size` | Array [width, height] | Original image dimensions in pixels |
| `metadata.processed_size` | Array [width, height] | Processed image dimensions (after resizing) |
| `metadata.filename` | String | Original filename of the uploaded image |
| `metadata.model` | String | Model used for OCR processing |

## 📱 Mobile Integration

You can send images from your phone using:

1. **HTTP Shortcuts App** (Android)
2. **Shortcuts App** (iOS)
3. **Any REST client** with multipart/form-data support

Example Shortcut:
```
POST http://your-server:5005/ocr
Content-Type: multipart/form-data
file: [Selected Photo]
```

## 🔒 Security Considerations

For production deployment:

1. **Add Authentication**: Implement API key or OAuth
2. **Use HTTPS**: Configure SSL/TLS
3. **Rate Limiting**: Add request throttling
4. **Input Validation**: Limit file sizes and types
5. **Network Security**: Use firewall rules

Example with API key (add to `app.py`):

```python
from fastapi import Header, HTTPException

API_KEY = os.getenv("API_KEY", "your-secret-key")

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

@app.post("/ocr", dependencies=[Depends(verify_api_key)])
async def process_ocr(file: UploadFile = File(...)):
    # ... rest of the code
```

## 🎯 Performance Optimization

### GPU Memory

- **Adjust VRAM usage**: Set `TARGET_IMAGE_DIM` lower if you have limited VRAM
- **Batch processing**: For multiple images, process sequentially to avoid OOM

### Model Loading

- First request will be slow (model loading)
- Subsequent requests are fast (~2-5 seconds per image)
- Models are cached in the `huggingface_cache` volume

### Scaling

For high-load scenarios:
- Deploy multiple instances behind a load balancer
- Use Redis for caching results
- Implement job queue (Celery/RQ)

## 🐛 Troubleshooting

### Out of Memory Errors

```bash
# Reduce image dimensions
docker run -e TARGET_IMAGE_DIM=800 ...
```

### Model Download Issues

```bash
# Pre-download models
docker exec -it olmocr-api python -c "from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration; AutoProcessor.from_pretrained('Qwen/Qwen2.5-VL-7B-Instruct'); Qwen2_5_VLForConditionalGeneration.from_pretrained('allenai/olmOCR-2-7B-1025-FP8')"
```

### GPU Not Detected

```bash
# Test NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Install nvidia-container-toolkit if needed
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

## 📊 Model Information

- **Model**: [olmOCR-2-7B-1025-FP8](https://huggingface.co/allenai/olmOCR-2-7B-1025-FP8)
- **Base Model**: Qwen2.5-VL-7B-Instruct
- **Quantization**: FP8 for efficient inference
- **Training**: SFT + GRPO RL fine-tuning
- **Performance**: 82.4% on olmOCR-Bench

## 📚 References

- [olmOCR GitHub](https://github.com/allenai/olmocr)
- [olmOCR Model Card](https://huggingface.co/allenai/olmOCR-2-7B-1025-FP8)
- [Research Paper](https://arxiv.org/abs/2502.18443)
- [Qwen2.5-VL](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct)

## 📄 License

This project uses models licensed under Apache 2.0. See the [olmOCR license](https://github.com/allenai/olmocr/blob/main/LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check the [olmOCR documentation](https://github.com/allenai/olmocr)
- Review the [model documentation](https://huggingface.co/allenai/olmOCR-2-7B-1025-FP8)

---

**Built with ❤️ using olmOCR by Allen AI**

