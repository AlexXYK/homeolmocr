# Portainer Deployment Guide

## 🚀 Deploy olmOCR API to Portainer (Port 5005)

Your image is now live on DockerHub: **`alexxyk/olmocr-api:latest`**

---

## Quick Deploy Steps

### 1. Open Portainer

Navigate to your Portainer web interface (usually `http://your-server:9000`)

### 2. Create New Stack

1. Click **Stacks** in the left menu
2. Click **+ Add stack** button
3. Enter stack name: `olmocr-api`

### 3. Paste Stack Configuration

Copy and paste this entire configuration:

```yaml
version: '3.8'

services:
  olmocr-api:
    image: alexxyk/olmocr-api:latest
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

### 4. Deploy

1. Scroll down
2. Click **Deploy the stack**
3. Wait for deployment (1-2 minutes)

### 5. Verify Deployment

#### Check Container Status
1. Go to **Containers** in Portainer
2. Find `olmocr-api` - should show "running"
3. Click on it to view logs

#### Check Logs
Look for:
```
✅ "Model and processor loaded successfully!"
✅ "Uvicorn running on http://0.0.0.0:5005"
```

#### Test API
Open your browser or use curl:
```bash
# Health check
curl http://your-server-ip:5005/health

# Expected response:
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cuda:0",
  "cuda_available": true
}
```

---

## 🎯 Access Your API

### From Anywhere

```bash
# Health check
curl http://your-server-ip:5005/health

# Process an image
curl -X POST -F "file=@image.jpg" http://your-server-ip:5005/ocr
```

### From Your Phone

**iOS Shortcuts:**
```
URL: http://your-server-ip:5005/ocr
Method: POST
Body Type: Form
Field: file = [Selected Photo]
```

**Android HTTP Shortcuts:**
```
URL: http://your-server-ip:5005/ocr
Method: POST
Body: Multipart
File parameter: file
```

---

## ⚙️ Configuration Options

### Adjust GPU Memory Usage

If you have limited VRAM, reduce image size:

```yaml
environment:
  - TARGET_IMAGE_DIM=800  # Lower = less VRAM, faster, slightly less accurate
```

### Use Different GPU

```yaml
environment:
  - CUDA_VISIBLE_DEVICES=1  # Use second GPU (0 = first, 1 = second, etc.)
```

### Multiple GPUs

```yaml
environment:
  - CUDA_VISIBLE_DEVICES=0,1  # Use GPUs 0 and 1
```

---

## 🔄 Update Your Deployment

When you push a new version to DockerHub:

### Option 1: Via Portainer UI
1. Go to **Stacks**
2. Click on `olmocr-api`
3. Click **Update the stack**
4. Enable **Pull latest image**
5. Click **Update**

### Option 2: Via Portainer API
```bash
# Pull latest image
docker pull alexxyk/olmocr-api:latest

# Recreate container
curl -X POST http://your-portainer:9000/api/stacks/{stackId}/recreate \
  -H "X-API-Key: your-api-key"
```

### Option 3: Manual
```bash
# SSH to your server
docker pull alexxyk/olmocr-api:latest
docker stop olmocr-api
docker rm olmocr-api

# Redeploy via Portainer UI
```

---

## 📊 Monitoring

### View Logs
1. In Portainer, go to **Containers**
2. Click `olmocr-api`
3. Click **Logs** tab
4. Enable **Auto-refresh**

### Resource Usage
1. In Portainer, go to **Containers**
2. Click `olmocr-api`
3. Click **Stats** tab
4. Monitor CPU, RAM, GPU usage

### Check GPU from Container
```bash
# Via Portainer Console
1. Click on container
2. Click "Console"
3. Connect
4. Run: nvidia-smi
```

---

## 🔧 Troubleshooting

### Container Won't Start

**Check logs in Portainer:**
1. Containers → olmocr-api → Logs

**Common issues:**
- GPU not available: Ensure NVIDIA Container Toolkit installed
- Port in use: Change port to `5006:5005`
- Out of memory: Reduce `TARGET_IMAGE_DIM`

### GPU Not Detected

**Solution 1:** Check NVIDIA runtime
```bash
# SSH to server
nvidia-smi  # Should show GPU
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

**Solution 2:** Install NVIDIA Container Toolkit
```bash
# On your server
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### Port Already in Use

**Change the port mapping:**
```yaml
ports:
  - "5006:5005"  # External:Internal
```

Then access at: `http://your-server:5006`

### Out of Memory

**Reduce image processing size:**
```yaml
environment:
  - TARGET_IMAGE_DIM=800  # or even lower: 640
```

---

## 🔒 Security (Optional but Recommended)

### Add API Key Authentication

Update the stack with:
```yaml
environment:
  - API_KEY=your-secure-random-key-here-change-this
```

Then modify `app.py` to check the key (see README.md for code example)

### Use Reverse Proxy

Add nginx or Traefik in front:
```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    # SSL configuration
    # Proxy to olmocr-api:5005
```

---

## 📈 Scaling

### Multiple Instances

For high load, run multiple instances:

```yaml
services:
  olmocr-api-1:
    image: alexxyk/olmocr-api:latest
    ports:
      - "5005:5005"
    # ... config ...
    
  olmocr-api-2:
    image: alexxyk/olmocr-api:latest
    ports:
      - "5006:5005"
    environment:
      - CUDA_VISIBLE_DEVICES=1  # Use different GPU
    # ... config ...
```

Then use a load balancer (nginx) in front.

---

## ✅ Success Checklist

```
□ Portainer stack deployed
□ Container shows "running" status
□ Logs show "Model and processor loaded successfully!"
□ Health endpoint returns {"status": "healthy"}
□ Can access from browser: http://server:5005/health
□ Test image processes successfully
□ Response time acceptable (2-5 seconds after warmup)
□ Can access from phone/remote devices
```

---

## 🎉 You're Live!

Your olmOCR API is now running on **port 5005**!

**API Endpoint:** `http://your-server-ip:5005`

**Health Check:** `http://your-server-ip:5005/health`

**OCR Endpoint:** `http://your-server-ip:5005/ocr` (POST with image file)

### Test It Now

```bash
# From your local machine
curl http://your-server-ip:5005/health

# Process an image
curl -X POST -F "file=@test.jpg" http://your-server-ip:5005/ocr
```

---

## 📞 Quick Reference

| What | Value |
|------|-------|
| DockerHub Image | `alexxyk/olmocr-api:latest` |
| Port | 5005 |
| Health Endpoint | `/health` |
| OCR Endpoint | `/ocr` (POST) |
| Method | POST with multipart/form-data |
| File Field | `file` |
| Response | JSON with `success`, `text`, `metadata` |

---

**Your API is ready to process millions of documents! 🚀**

