# DockerHub Setup Guide

## Creating a New DockerHub Repository

### Step 1: Sign Up / Log In

1. Go to [https://hub.docker.com](https://hub.docker.com)
2. Click **Sign Up** (or **Sign In** if you have an account)
3. Create a free account (allows unlimited public repositories)

### Step 2: Create Repository

#### Option A: Via Web Interface (Easiest)

1. Log into DockerHub
2. Click **Repositories** in the top menu
3. Click **Create Repository** button
4. Fill in:
   - **Name**: `olmocr-api` (must be lowercase, can use hyphens)
   - **Description**: "OCR API using olmOCR-2-7B-1025-FP8 for converting images to markdown"
   - **Visibility**: Public (or Private if you have a paid plan)
5. Click **Create**

Your repository will be at: `docker.io/yourusername/olmocr-api`

#### Option B: Automatic Creation (When You Push)

DockerHub automatically creates public repositories when you push to them for the first time. Just push and it will be created!

### Step 3: Login from Command Line

```bash
# Login to DockerHub
docker login

# Enter your DockerHub username and password
# Username: yourusername
# Password: ************
```

**Important**: Your username must be lowercase!

### Step 4: Tag Your Image

```bash
# Format: docker tag local-image:tag dockerhub-username/repo-name:tag
docker tag olmocr-api:latest yourusername/olmocr-api:latest

# Example with my username:
docker tag olmocr-api:latest johndoe/olmocr-api:latest
```

### Step 5: Push to DockerHub

```bash
# Push the image
docker push yourusername/olmocr-api:latest

# This will upload ~15GB (takes 10-30 minutes depending on your upload speed)
```

You'll see output like:
```
The push refers to repository [docker.io/yourusername/olmocr-api]
a1b2c3d4e5f6: Pushing [==>                    ] 1.234GB/15.67GB
...
```

### Step 6: Verify

Go to `https://hub.docker.com/r/yourusername/olmocr-api` and you should see your repository!

## Complete Build & Push Workflow

### Automated Script Method (Recommended)

```bash
# Set your DockerHub username
export DOCKER_USERNAME=yourusername

# Run the automated script
bash build_and_push.sh
```

The script will:
1. ✅ Build the Docker image
2. ✅ Tag it properly
3. ✅ Prompt for DockerHub login
4. ✅ Push to your repository
5. ✅ Provide deployment instructions

### Manual Method

```bash
# 1. Build the image
docker build -t olmocr-api:latest .

# 2. Tag for DockerHub
docker tag olmocr-api:latest yourusername/olmocr-api:latest

# 3. Login
docker login

# 4. Push
docker push yourusername/olmocr-api:latest

# 5. Verify
docker pull yourusername/olmocr-api:latest
```

## Using Your Image from DockerHub

### Pull and Run

Anyone can now pull and run your image:

```bash
# Pull the image
docker pull yourusername/olmocr-api:latest

# Run it
docker run --gpus all -p 5005:5005 yourusername/olmocr-api:latest
```

### Update docker-compose.yml

Replace `yourusername` with your actual DockerHub username:

```yaml
services:
  olmocr-api:
    image: yourusername/olmocr-api:latest  # <-- Update this line
    # ... rest of config
```

### Deploy to Portainer

1. Go to **Stacks** → **Add Stack**
2. Paste the docker-compose.yml content
3. Update the image name to match your DockerHub username
4. Click **Deploy**

Portainer will automatically pull from DockerHub!

## Updating Your Image

When you make changes:

```bash
# 1. Rebuild
docker build -t yourusername/olmocr-api:latest .

# 2. Push
docker push yourusername/olmocr-api:latest

# 3. Update running containers
docker pull yourusername/olmocr-api:latest
docker-compose up -d --force-recreate
```

## DockerHub Repository Settings

### Make it Professional

1. Go to your repository on DockerHub
2. Click **Settings** tab
3. Add:
   - **Short Description**: One-line summary
   - **Full Description**: Copy from README.md
   - **Categories**: Add relevant tags

### Example Full Description (Markdown Supported)

```markdown
# olmOCR API

Production-ready OCR API using olmOCR-2-7B-1025-FP8 model.

## Features
- High-accuracy OCR
- Markdown output
- GPU accelerated
- REST API
- Mobile-friendly

## Quick Start

```bash
docker run --gpus all -p 5005:5005 yourusername/olmocr-api:latest
```

## Documentation
See [GitHub Repository](your-github-url) for full documentation.

## API Usage

```bash
curl -X POST -F "file=@image.jpg" http://localhost:5005/ocr
```
```

### Add Tags

Suggested tags:
- `ocr`
- `ai`
- `machine-learning`
- `vision-language-model`
- `api`
- `document-processing`
- `qwen`
- `transformers`

## Multi-Platform Support (Optional)

If you want to support multiple architectures:

```bash
# Build for multiple platforms (requires buildx)
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 \
  -t yourusername/olmocr-api:latest --push .
```

## Private vs Public Repository

### Public (Free)
- ✅ Unlimited pulls
- ✅ Anyone can access
- ✅ Good for open source
- ❌ Code/image is public

### Private (Paid)
- ✅ Access control
- ✅ Private code
- ❌ Costs money
- ❌ Limited pulls on free tier

## Common Issues

### "Denied: requested access to the resource is denied"

**Solution**: Your username doesn't match or you're not logged in
```bash
docker login
# Make sure username matches: yourusername/olmocr-api
```

### "unauthorized: authentication required"

**Solution**: Login expired
```bash
docker logout
docker login
```

### Push is very slow

**Solution**: This is normal! The image is ~15GB
- First push: 10-30 minutes depending on upload speed
- Subsequent pushes: Only changed layers upload (faster)

### "denied: requested access to the resource is denied" when pulling

**Solution**: Repository is private or doesn't exist
- Check the repository exists on DockerHub
- Check spelling of username/repo name
- Make sure repository is public

## Best Practices

1. **Use Tags**: Version your images
   ```bash
   docker tag olmocr-api:latest yourusername/olmocr-api:v1.0.0
   docker push yourusername/olmocr-api:v1.0.0
   docker push yourusername/olmocr-api:latest
   ```

2. **Add README**: Update DockerHub repository description

3. **Regular Updates**: Keep dependencies updated
   ```bash
   docker build --no-cache -t yourusername/olmocr-api:latest .
   ```

4. **Automated Builds**: Link GitHub to DockerHub for auto-builds

5. **Security Scanning**: Enable Docker Hub's security scanning

## GitHub to DockerHub Auto-Build (Optional)

1. In DockerHub, go to **Account Settings** → **Linked Accounts**
2. Link your GitHub account
3. In your repository, go to **Builds** tab
4. Configure automated builds from your GitHub repo
5. Every push to GitHub will trigger a Docker build

## Summary Checklist

- [ ] DockerHub account created
- [ ] Repository created: `yourusername/olmocr-api`
- [ ] Docker image built locally
- [ ] Image tagged correctly
- [ ] Logged into DockerHub via CLI
- [ ] Image pushed successfully
- [ ] docker-compose.yml updated with your username
- [ ] Tested pulling the image
- [ ] Repository description added
- [ ] Ready to deploy to Portainer!

## Quick Reference

```bash
# Login
docker login

# Build
docker build -t yourusername/olmocr-api:latest .

# Push
docker push yourusername/olmocr-api:latest

# Pull (test)
docker pull yourusername/olmocr-api:latest

# Run
docker run --gpus all -p 5005:5005 yourusername/olmocr-api:latest
```

---

**You're ready to share your API with the world! 🚀**

