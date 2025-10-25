# 🚀 START HERE - Your Complete olmOCR API Setup

**Welcome!** This is your one-page guide to get from zero to production in 30 minutes.

## What You're Getting

A production-ready OCR API that:
- ✅ Converts images to markdown via REST API
- ✅ Uses state-of-the-art AI (olmOCR-2-7B-1025-FP8)
- ✅ Runs on your GPU (16GB+ VRAM required)
- ✅ Works from phone/computer/any HTTP client
- ✅ Deployable via Docker + Portainer
- ✅ Port 5005 (as requested)

## 🎯 Three Simple Steps

### STEP 1: Create DockerHub Account (5 minutes)

```
1. Go to https://hub.docker.com
2. Click "Sign Up"
3. Create account (free)
4. Click "Create Repository"
   - Name: olmocr-api
   - Visibility: Public
   - Click "Create"

Your repo URL: docker.io/YOUR-USERNAME/olmocr-api
```

**Need help?** → See `DOCKERHUB_SETUP.md`

### STEP 2: Build & Push (20 minutes)

```bash
# Set your DockerHub username
export DOCKER_USERNAME=your-dockerhub-username

# Build the image (takes 5-10 minutes)
docker build -t $DOCKER_USERNAME/olmocr-api:latest .

# Login to DockerHub
docker login

# Push to DockerHub (takes 10-15 minutes, ~15GB upload)
docker push $DOCKER_USERNAME/olmocr-api:latest
```

**Automated option:**
```bash
export DOCKER_USERNAME=your-dockerhub-username
bash build_and_push.sh
```

### STEP 3: Deploy & Test (5 minutes)

#### Option A: Test Locally First

```bash
# Run container
docker run --gpus all -p 5005:5005 $DOCKER_USERNAME/olmocr-api:latest

# Wait for: "Model and processor loaded successfully!"

# In another terminal, test with your images:
python test_api.py "C:\Users\alexa\OneDrive\Pictures\grandmatest.jpg"
```

#### Option B: Deploy to Portainer

```
1. Open Portainer
2. Stacks → Add Stack
3. Name: olmocr-api
4. Paste docker-compose.yml contents
5. Update line with your username:
   image: YOUR-USERNAME/olmocr-api:latest
6. Deploy
7. Wait 2 minutes for model download
8. Test: curl http://your-server:5005/health
```

## 🎉 You're Done!

Your API is now live at `http://your-server:5005`

### Test It

```bash
# Health check
curl http://localhost:5005/health

# Process image
curl -X POST -F "file=@image.jpg" http://localhost:5005/ocr

# Or use the test script
python test_api.py "path/to/image.jpg"
```

### Use from Phone

**iOS Shortcuts:**
```
POST http://your-server-ip:5005/ocr
Body: Multipart form-data
Field: "file" = Selected Photo
```

**Android HTTP Shortcuts:**
```
URL: http://your-server-ip:5005/ocr
Method: POST
Body: Multipart
File field: "file"
```

## 📚 Documentation Map

- **START_HERE.md** ← You are here (quick setup)
- **DOCKERHUB_SETUP.md** ← Detailed DockerHub instructions
- **QUICKSTART.md** ← Step-by-step guide with examples
- **TEST_AFTER_DEPLOY.md** ← Complete testing checklist
- **README.md** ← Full documentation
- **DEPLOYMENT.md** ← Advanced deployment options
- **PROJECT_STATUS.md** ← What's built and ready

## 🔧 Quick Commands Reference

```bash
# Build
docker build -t yourusername/olmocr-api:latest .

# Push
docker push yourusername/olmocr-api:latest

# Run locally
docker run --gpus all -p 5005:5005 yourusername/olmocr-api:latest

# Pull on another machine
docker pull yourusername/olmocr-api:latest

# Check health
curl http://localhost:5005/health

# Test OCR
python test_api.py "image.jpg"

# View logs
docker logs olmocr-api

# Restart
docker restart olmocr-api
```

## ⚡ Troubleshooting

**Container won't start?**
```bash
docker logs olmocr-api
nvidia-smi  # Check GPU
```

**Can't push to DockerHub?**
```bash
docker login
# Make sure username matches: yourusername/olmocr-api
```

**API timeout?**
- First request takes 30-60 seconds (normal - model loading)
- Subsequent requests: 2-5 seconds

**Out of memory?**
```bash
# Reduce image size
docker run -e TARGET_IMAGE_DIM=800 ...
```

## 🎯 What's Next?

1. ✅ **Test with your images** (vettest.jpg, grandmatest.jpg)
2. ✅ **Access from your phone** using shortcuts
3. ✅ **Share the API** with others
4. 🔒 **Add authentication** (see README.md for code example)
5. 🌐 **Set up HTTPS** (for production use)
6. 📊 **Monitor usage** (optional)

## 💡 Pro Tips

1. **Model caching**: First run downloads ~14GB, then it's cached
2. **Fast restarts**: Subsequent starts are instant (model cached)
3. **Batch processing**: Process multiple images via `example_usage.py`
4. **Custom prompts**: Modify `build_prompt()` in `app.py` for specific needs
5. **GPU memory**: If OOM, reduce `TARGET_IMAGE_DIM` environment variable

## 📊 Expected Performance

- **First request**: 30-60 seconds (one-time model load)
- **Subsequent requests**: 2-5 seconds per image
- **Accuracy**: 82.4% on olmOCR-Bench
- **Throughput**: ~12-30 images/minute

## 🆘 Need Help?

1. **Check logs**: `docker logs olmocr-api`
2. **Run validation**: `python check_setup.py`
3. **Test suite**: See `TEST_AFTER_DEPLOY.md`
4. **Full docs**: See `README.md`

## ✅ Success Checklist

```
Before pushing to DockerHub:
□ Docker installed and running
□ NVIDIA GPU with 16GB+ VRAM
□ DockerHub account created
□ Repository created on DockerHub

After pushing:
□ Image pushed successfully
□ docker-compose.yml updated with your username
□ Can pull image: docker pull yourusername/olmocr-api:latest

After deploying:
□ Container running: docker ps
□ Health check passes: curl http://localhost:5005/health
□ Test image processes successfully
□ Can access from remote (if deployed remotely)

Production ready:
□ Tested with both your images (vettest.jpg, grandmatest.jpg)
□ Response times acceptable
□ Mobile access working (if needed)
□ Monitoring set up (optional)
□ Backups configured (optional)
```

## 🎊 You're All Set!

Your olmOCR API is ready to process millions of documents!

**Questions?** Check the detailed docs in the files listed above.

**Ready to build?** Run these three commands:

```bash
# 1. Build
docker build -t yourusername/olmocr-api:latest .

# 2. Login & Push
docker login
docker push yourusername/olmocr-api:latest

# 3. Deploy
# Use Portainer with docker-compose.yml OR:
docker run --gpus all -p 5005:5005 yourusername/olmocr-api:latest
```

---

**Built with ❤️ for document processing excellence**

*Need the absolute shortest path? Just run: `export DOCKER_USERNAME=yourusername && bash build_and_push.sh`*

