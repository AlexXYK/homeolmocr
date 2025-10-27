# 🎯 FINAL DEPLOYMENT - Smart Version for Your Setup

## Your Perfect Setup:

```
GPU 0: Ollama + ComfyUI (your main workflow)
GPU 1: olmOCR (loads on-demand, unloads when idle)
```

---

## 🚀 Deploy the Smart Version

### Step 1: Stop Old VLLM Stack

**In Portainer:**
1. Go to **Stacks**
2. Find your **olmocr** stack
3. Click **Stop** (or **Delete** if you want to remove it)
4. Wait for containers to stop

---

### Step 2: Deploy Smart Stack

**In Portainer:**
1. Go to **Stacks** → **Add Stack**
2. Name: `olmocr-smart`
3. **Paste this:**

```yaml
version: '3.8'

services:
  olmocr-api:
    image: alexxyk/olmocr-api:smart
    container_name: olmocr-api-smart
    ports:
      - "5006:5005"
    environment:
      # API Configuration
      - PORT=5005
      
      # Model Configuration
      - MODEL_NAME=allenai/olmOCR-2-7B-1025-FP8
      - PROCESSOR_NAME=Qwen/Qwen2.5-VL-7B-Instruct
      - TARGET_IMAGE_DIM=1024
      
      # Smart Memory Management
      - KEEP_ALIVE_SECONDS=300        # Keep model loaded for 5 minutes after last use
                                       # Adjust: 60=1min, 300=5min, 600=10min
      
      # GPU Configuration - Uses GPU 1 (leaves GPU 0 free!)
      - NVIDIA_VISIBLE_DEVICES=1
      - PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
      
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
      start_period: 30s

volumes:
  huggingface_cache:
    driver: local
```

4. Click **Deploy the stack**
5. Wait 30 seconds

---

### Step 3: Test

```bash
# Check status
curl http://192.168.0.153:5006/status

# Should show: "model_loaded": false (not loaded yet - GPU free!)

# Now send an image
py test_api.py "C:\Users\alexa\OneDrive\Pictures\Samsung Gallery\Pictures\Office Lens\vettest.jpg" http://192.168.0.153:5006

# First request: ~60 seconds (loads model)
# Model stays loaded for 5 minutes
# After 5 minutes idle: Auto-unloads, GPU 1 free again!
```

---

## 📊 How It Works:

### Timeline:
```
t=0:00  → API starts, GPU 1 empty ✅
t=0:05  → You send image
t=0:05  → Model loads (60s)
t=1:05  → OCR processes (3s)
t=1:08  → Response sent
        → 5-min timer starts
t=6:08  → Model auto-unloads
        → GPU 1 free again! ✅
```

### If You Send Multiple Images:
```
Image 1 → Load model (60s) → Process (3s)
Image 2 (10s later) → Process (3s) ← Already loaded!
Image 3 (20s later) → Process (3s) ← Still loaded!
...
5 min idle → Unload
```

---

## 🎮 GPU Usage:

### While Idle (Most of the Time):
```
GPU 0: Ollama ready ✅
GPU 1: Empty ✅
```

### During OCR:
```
GPU 0: Ollama ready ✅
GPU 1: olmOCR running (10-12GB)
```

### 5 Minutes After OCR:
```
GPU 0: Ollama ready ✅
GPU 1: Empty again ✅
```

---

## ⚙️ Tunable Settings:

**Adjust keep-alive time:**
```yaml
- KEEP_ALIVE_SECONDS=60    # 1 minute (unloads faster)
- KEEP_ALIVE_SECONDS=300   # 5 minutes (default)
- KEEP_ALIVE_SECONDS=600   # 10 minutes (stays loaded longer)
- KEEP_ALIVE_SECONDS=3600  # 1 hour (rarely unloads)
```

**Adjust image size (for faster processing):**
```yaml
- TARGET_IMAGE_DIM=800   # Faster, uses less VRAM
- TARGET_IMAGE_DIM=1024  # Balanced (default)
- TARGET_IMAGE_DIM=1288  # Best quality, slower
```

---

## 🆚 Version Comparison:

| Version | GPU Usage | Speed | Best For |
|---------|-----------|-------|----------|
| **Smart** ⭐ | Loads/unloads | 60s first, 3s after | **Your setup!** 2 GPUs, shared use |
| VLLM | Always loaded | 3s always | Production, dedicated GPU |
| Transformers | Always loaded | 5s always | Testing only |

---

## 📋 Quick Commands:

```bash
# Check if model is loaded
curl http://192.168.0.153:5006/status

# Process image (auto-loads if needed)
curl -X POST -F "file=@image.jpg" http://192.168.0.153:5006/ocr

# Check GPU 1 usage
nvidia-smi
```

---

**Deploy the smart stack in Portainer and you're golden!** 🎉

This gives you the best of both worlds:
- ✅ Fast OCR when you need it
- ✅ GPU freed for Ollama/ComfyUI when you don't
- ✅ Simple, one container
- ✅ Configurable keep-alive time

**Ready to deploy?** Just stop the old VLLM stack and deploy `portainer-stack-smart.yml`!
