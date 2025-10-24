# Deployment Guide for olmOCR API

This guide covers deployment options for the olmOCR API service.

## Quick Start

### 1. Build and Test Locally

```bash
# Build the image
docker build -t olmocr-api .

# Test locally
docker run --gpus all -p 5005:5005 olmocr-api

# In another terminal, test the API
python test_api.py path/to/test/image.jpg
```

### 2. Push to Docker Hub

```bash
# Use the build script
chmod +x build_and_push.sh
./build_and_push.sh

# Or manually
docker login
docker tag olmocr-api yourusername/olmocr-api:latest
docker push yourusername/olmocr-api:latest
```

### 3. Deploy with Portainer

1. Log into Portainer
2. Go to **Stacks** → **Add Stack**
3. Name: `olmocr-api`
4. Copy/paste `docker-compose.yml` content
5. Update environment variable `DOCKER_USERNAME`
6. Click **Deploy the stack**

## Portainer Stack Configuration

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
      - CUDA_VISIBLE_DEVICES=0
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
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5005/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s

volumes:
  huggingface_cache:
    driver: local
```

## Alternative Deployment Options

### Docker Compose (Local)

```bash
# Start the stack
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the stack
docker-compose down
```

### Docker Run (Simple)

```bash
docker run -d \
  --name olmocr-api \
  --gpus all \
  -p 5005:5005 \
  -v huggingface_cache:/root/.cache/huggingface \
  -e MODEL_NAME=allenai/olmOCR-2-7B-1025-FP8 \
  --restart unless-stopped \
  yourusername/olmocr-api:latest
```

### Kubernetes

Create `olmocr-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: olmocr-api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: olmocr-api
  template:
    metadata:
      labels:
        app: olmocr-api
    spec:
      containers:
      - name: olmocr-api
        image: yourusername/olmocr-api:latest
        ports:
        - containerPort: 5005
        env:
        - name: MODEL_NAME
          value: "allenai/olmOCR-2-7B-1025-FP8"
        - name: PROCESSOR_NAME
          value: "Qwen/Qwen2.5-VL-7B-Instruct"
        resources:
          limits:
            nvidia.com/gpu: 1
        volumeMounts:
        - name: cache
          mountPath: /root/.cache/huggingface
      volumes:
      - name: cache
        persistentVolumeClaim:
          claimName: huggingface-cache-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: olmocr-api-service
spec:
  selector:
    app: olmocr-api
  ports:
  - protocol: TCP
    port: 5005
    targetPort: 5005
  type: LoadBalancer
```

Deploy:
```bash
kubectl apply -f olmocr-deployment.yaml
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 5005 | API port |
| `MODEL_NAME` | allenai/olmOCR-2-7B-1025-FP8 | Model to use |
| `PROCESSOR_NAME` | Qwen/Qwen2.5-VL-7B-Instruct | Processor/tokenizer |
| `TARGET_IMAGE_DIM` | 1288 | Max image dimension |
| `CUDA_VISIBLE_DEVICES` | 0 | GPU device(s) to use |

## System Requirements

### Minimum Requirements
- **GPU**: NVIDIA GPU with 16GB VRAM
- **RAM**: 32GB system RAM
- **Storage**: 50GB for model and cache
- **CUDA**: 11.8 or higher

### Recommended Requirements
- **GPU**: NVIDIA A100, A6000, or RTX 4090
- **RAM**: 64GB system RAM
- **Storage**: 100GB SSD
- **CUDA**: 12.1

## Monitoring

### Health Check

```bash
curl http://localhost:5005/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cuda:0",
  "cuda_available": true
}
```

### Container Logs

```bash
# Docker
docker logs -f olmocr-api

# Docker Compose
docker-compose logs -f

# Portainer
View logs in the Portainer UI under Containers
```

### Resource Usage

```bash
# GPU usage
nvidia-smi

# Container stats
docker stats olmocr-api
```

## Troubleshooting

### Container Won't Start

**Issue**: Container exits immediately
```bash
# Check logs
docker logs olmocr-api

# Common causes:
# 1. GPU not available - check nvidia-smi
# 2. Out of memory - reduce TARGET_IMAGE_DIM
# 3. Model download failed - check network
```

### Out of Memory

**Issue**: CUDA out of memory errors
```bash
# Solution 1: Reduce image size
docker run -e TARGET_IMAGE_DIM=800 ...

# Solution 2: Clear GPU memory
nvidia-smi --gpu-reset

# Solution 3: Use smaller batch size (code modification needed)
```

### Model Download Issues

**Issue**: Model fails to download
```bash
# Solution: Pre-download models
docker exec -it olmocr-api bash
python -c "
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
AutoProcessor.from_pretrained('Qwen/Qwen2.5-VL-7B-Instruct')
Qwen2_5_VLForConditionalGeneration.from_pretrained('allenai/olmOCR-2-7B-1025-FP8')
"
```

### Slow Performance

**Issue**: API responses are very slow

**Solutions**:
1. First request is always slow (model loading) - this is normal
2. Ensure GPU is being used: check logs for "cuda:0"
3. Reduce image dimensions if too large
4. Check GPU utilization with `nvidia-smi`

## Security Best Practices

1. **API Authentication**
   - Add API key authentication
   - Use OAuth2 for production

2. **Network Security**
   - Use reverse proxy (nginx)
   - Enable HTTPS/TLS
   - Restrict port access

3. **Rate Limiting**
   - Add request throttling
   - Implement queue system

4. **Input Validation**
   - Limit file sizes (10MB default)
   - Validate file types
   - Sanitize inputs

## Scaling Considerations

### Horizontal Scaling

For high load:
1. Deploy multiple instances
2. Use load balancer (nginx/HAProxy)
3. Implement job queue (Redis/RabbitMQ)

Example nginx configuration:
```nginx
upstream olmocr_backend {
    least_conn;
    server olmocr-1:5005;
    server olmocr-2:5005;
    server olmocr-3:5005;
}

server {
    listen 80;
    location / {
        proxy_pass http://olmocr_backend;
    }
}
```

### Vertical Scaling

For better performance:
1. Use more powerful GPU (A100 vs RTX 3090)
2. Increase system RAM
3. Use faster storage (NVMe SSD)

## Backup and Recovery

### Backup Model Cache

```bash
# Backup
docker run --rm -v huggingface_cache:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/huggingface_cache_backup.tar.gz /data

# Restore
docker run --rm -v huggingface_cache:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/huggingface_cache_backup.tar.gz -C /
```

### Container Updates

```bash
# Pull new version
docker pull yourusername/olmocr-api:latest

# Stop old container
docker stop olmocr-api

# Remove old container
docker rm olmocr-api

# Start new container
docker run -d --name olmocr-api ... yourusername/olmocr-api:latest
```

## Production Checklist

- [ ] Environment variables configured
- [ ] GPU detected and working
- [ ] Health check endpoint responding
- [ ] Model loaded successfully
- [ ] Test images processed correctly
- [ ] Logs being captured
- [ ] Monitoring configured
- [ ] Backups configured
- [ ] Security hardening applied
- [ ] Documentation updated

## Support

For issues:
1. Check logs: `docker logs olmocr-api`
2. Verify GPU: `nvidia-smi`
3. Test health: `curl localhost:5005/health`
4. Review this guide
5. Check GitHub issues

---

**Last Updated**: 2025-10-24

