# Testing After Deployment

This guide helps you test your olmOCR API after deploying to ensure everything works perfectly.

## Quick Smoke Test (2 minutes)

### 1. Check Container is Running

```bash
docker ps | grep olmocr-api
```

Expected output:
```
CONTAINER ID   IMAGE                    STATUS          PORTS
abc123def456   yourusername/olmocr-api  Up 5 minutes    0.0.0.0:5005->5005/tcp
```

### 2. Check Logs

```bash
docker logs olmocr-api --tail 50
```

Look for:
```
✅ "Model and processor loaded successfully!"
✅ "Uvicorn running on http://0.0.0.0:5005"
```

### 3. Health Check

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

### 4. Test OCR with Your Images

```bash
# Test image 1
python test_api.py "C:\Users\alexa\OneDrive\Pictures\grandmatest.jpg"

# Test image 2  
python test_api.py "C:\Users\alexa\OneDrive\Pictures\Samsung Gallery\Pictures\Office Lens\vettest.jpg"
```

Expected output:
```
📸 Testing OCR with: grandmatest.jpg
🌐 API URL: http://localhost:5005
🔍 Checking API health...
✅ Health check: {...}
🚀 Sending image for OCR processing...
✅ OCR processing successful!
================================================================================
EXTRACTED TEXT:
================================================================================
[Your extracted text in markdown format]
================================================================================
💾 Output saved to: grandmatest_ocr.md
```

## Detailed Testing

### Test 1: Root Endpoint

```bash
curl http://localhost:5005/
```

Expected:
```json
{
  "service": "olmOCR API",
  "version": "1.0.0",
  "status": "ready",
  "endpoints": {...}
}
```

### Test 2: Health Endpoint

```bash
curl http://localhost:5005/health
```

Expected:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cuda:0",
  "cuda_available": true
}
```

### Test 3: OCR Processing

```bash
# Using curl
curl -X POST -F "file=@C:\Users\alexa\OneDrive\Pictures\grandmatest.jpg" \
  http://localhost:5005/ocr
```

Expected:
```json
{
  "success": true,
  "text": "# [Extracted Text]\n\n[Content here...]",
  "metadata": {
    "original_size": [width, height],
    "processed_size": [width, height],
    "filename": "grandmatest.jpg",
    "model": "allenai/olmOCR-2-7B-1025-FP8"
  }
}
```

### Test 4: Error Handling

```bash
# Send invalid file
echo "not an image" > test.txt
curl -X POST -F "file=@test.txt" http://localhost:5005/ocr
rm test.txt
```

Expected:
```json
{
  "success": false,
  "error": "Invalid image file: ..."
}
```

## Performance Testing

### Test 5: Response Time

```bash
# First request (cold start)
time curl -X POST -F "file=@your-image.jpg" http://localhost:5005/ocr > /dev/null

# Second request (warm)
time curl -X POST -F "file=@your-image.jpg" http://localhost:5005/ocr > /dev/null
```

Expected:
- First request: 30-60 seconds (model loading)
- Second request: 2-10 seconds (depends on image complexity)

### Test 6: Multiple Images

```bash
# Run the batch test
python example_usage.py
```

This will test both your images and show:
- ✅ Simple OCR
- ✅ Error handling
- ✅ Batch processing
- ✅ File saving

## Remote Testing (After Portainer Deploy)

### From Another Machine

```bash
# Replace with your server IP
SERVER_IP=192.168.1.100

# Health check
curl http://${SERVER_IP}:5005/health

# OCR test
curl -X POST -F "file=@image.jpg" http://${SERVER_IP}:5005/ocr
```

### From Your Phone

#### iOS Shortcut Test

1. Open Safari on iPhone
2. Go to: `http://your-server-ip:5005/health`
3. Should see JSON health status
4. Use the Shortcut from QUICKSTART.md

#### Android Test

1. Install **HTTP Request Shortcuts** app
2. Create test request to `http://your-server-ip:5005/health`
3. Test OCR with image from gallery

## Load Testing (Optional)

### Test 10 Requests

```bash
# Create a simple load test
for i in {1..10}; do
  echo "Request $i"
  curl -X POST -F "file=@image.jpg" http://localhost:5005/ocr -s > /dev/null &
done
wait
echo "All requests completed"
```

### Monitor GPU Usage

```bash
# In another terminal
watch -n 1 nvidia-smi
```

Monitor:
- GPU utilization
- Memory usage
- Temperature

## Troubleshooting Tests

### If Health Check Fails

```bash
# Check if container is running
docker ps -a | grep olmocr-api

# Check logs
docker logs olmocr-api

# Restart container
docker restart olmocr-api

# Wait 30 seconds for model to load
sleep 30

# Try again
curl http://localhost:5005/health
```

### If OCR Fails

```bash
# Check image file exists
ls -lh "your-image.jpg"

# Check file size (should be reasonable)
# Very large files might timeout

# Try with a smaller test image
curl -X POST -F "file=@small-test.jpg" http://localhost:5005/ocr
```

### If Getting Timeout

```bash
# Increase timeout
curl --max-time 300 -X POST -F "file=@image.jpg" http://localhost:5005/ocr
```

### If GPU Not Detected

```bash
# Check GPU from host
nvidia-smi

# Check GPU from container
docker exec olmocr-api nvidia-smi

# Check CUDA in Python
docker exec olmocr-api python -c "import torch; print(torch.cuda.is_available())"
```

## Success Criteria

Your deployment is successful if:

- ✅ Container is running
- ✅ Health endpoint returns "healthy"
- ✅ GPU is detected (cuda_available: true)
- ✅ Model is loaded (model_loaded: true)
- ✅ OCR processes test images successfully
- ✅ Output is valid markdown
- ✅ Response time is reasonable (2-10 seconds after warmup)
- ✅ Container restarts automatically
- ✅ Can access from remote machines (if deployed remotely)

## Test Checklist

Use this to verify your deployment:

```
□ Container running
□ No errors in logs
□ Health check passes
□ GPU detected
□ Model loaded
□ Test image 1 (grandmatest.jpg) processes successfully
□ Test image 2 (vettest.jpg) processes successfully
□ Output is valid markdown
□ Response time acceptable
□ Error handling works
□ Can access remotely (if applicable)
□ Restart policy working
□ Mobile access working (if applicable)
```

## Automated Test Script

```bash
#!/bin/bash
# save as: run_all_tests.sh

echo "=== olmOCR API Test Suite ==="

# Test 1: Container running
echo "Test 1: Checking container..."
if docker ps | grep -q olmocr-api; then
    echo "✅ Container running"
else
    echo "❌ Container not running"
    exit 1
fi

# Test 2: Health check
echo "Test 2: Health check..."
if curl -s http://localhost:5005/health | grep -q "healthy"; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

# Test 3: OCR test
echo "Test 3: OCR processing..."
if curl -s -X POST -F "file=@test_image.jpg" http://localhost:5005/ocr | grep -q "success"; then
    echo "✅ OCR processing works"
else
    echo "❌ OCR processing failed"
    exit 1
fi

echo "=== All tests passed! ==="
```

## Next Steps After Testing

Once all tests pass:

1. ✅ Document your DockerHub image URL
2. ✅ Save your docker-compose.yml configuration
3. ✅ Set up monitoring (optional)
4. ✅ Configure backups (optional)
5. ✅ Add authentication (recommended for production)
6. ✅ Set up HTTPS (recommended for production)
7. ✅ Create API documentation for your users
8. ✅ Enjoy your production OCR API! 🎉

---

**Your olmOCR API is ready for production use!**

