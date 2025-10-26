# Which Version Should I Use?

## 🚀 TL;DR: Use VLLM Version!

**For 16GB GPU (4070/5070)**: Use the **VLLM version** - it's 2-3x more memory efficient.

---

## Two Versions Available

### 1️⃣ VLLM Version (RECOMMENDED) ⭐

**Image**: `alexxyk/olmocr-api:vllm`  
**Stack**: `portainer-stack-vllm.yml`

✅ **Best for:**
- 16GB GPUs (RTX 4070, 5070, 3090)
- Production deployments
- Multiple concurrent requests
- Long-running services

✅ **Advantages:**
- Uses only 10-12GB GPU memory (vs 14.6GB)
- Model loads once, stays loaded
- 2-3x faster inference (1-3s vs 3-5s)
- Handles concurrent requests efficiently
- No OOM errors!

❌ **Disadvantages:**
- Two containers (VLLM server + API wrapper)
- Slightly more complex setup
- First startup takes 2-3 minutes

**Deploy:** See `VLLM_SETUP.md`

---

### 2️⃣ Transformers Version (Legacy)

**Image**: `alexxyk/olmocr-api:latest`  
**Stack**: `portainer-stack.yml`

✅ **Best for:**
- 24GB+ GPUs
- Testing/development
- Simple single-container setup

❌ **Disadvantages:**
- Uses 14.6GB GPU memory
- OOM errors on 16GB GPUs
- Slower inference
- No concurrent request optimization

---

## Quick Comparison

| Feature | VLLM | Transformers |
|---------|------|--------------|
| GPU Memory | 10-12GB ✨ | 14.6GB 💀 |
| 16GB GPU | Perfect! | Struggles |
| Speed | 1-3s | 3-5s |
| Concurrent | Yes | No |
| Setup | 2 containers | 1 container |
| Load Time | Once | Every request |
| OOM Errors | Rare | Common |

---

## Deployment Commands

### VLLM (Recommended)
```bash
# Portainer: Use portainer-stack-vllm.yml
# Docker Compose:
docker-compose -f docker-compose-vllm.yml up -d

# Access at: http://localhost:5005
```

### Transformers (Legacy)
```bash
# Portainer: Use portainer-stack.yml
# Docker Compose:
docker-compose up -d

# Access at: http://localhost:5005
```

---

## Migration Path

Already running the Transformers version? Upgrade:

```bash
# Stop old version
docker-compose down

# Start VLLM version
docker-compose -f docker-compose-vllm.yml up -d
```

**Same API, just faster and more efficient!** 🚀

---

## Need Help?

- **VLLM Setup**: Read `VLLM_SETUP.md`
- **API Usage**: Same for both versions, see `README.md`
- **Troubleshooting**: Check logs with `docker logs olmocr-vllm-server`

**Recommendation**: Start with VLLM. It's the way olmOCR was meant to be run!

