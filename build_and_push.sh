#!/bin/bash
# Build and push script for olmOCR API

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOCKER_USERNAME=${DOCKER_USERNAME:-yourusername}
IMAGE_NAME="olmocr-api"
TAG=${TAG:-latest}
FULL_IMAGE="${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}olmOCR API - Build and Push${NC}"
echo -e "${GREEN}================================================${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Prompt for Docker username if not set
if [ "$DOCKER_USERNAME" = "yourusername" ]; then
    echo -e "${YELLOW}⚠️  Please set DOCKER_USERNAME environment variable${NC}"
    read -p "Enter your Docker Hub username: " DOCKER_USERNAME
    FULL_IMAGE="${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"
fi

echo ""
echo -e "${YELLOW}Building image: ${FULL_IMAGE}${NC}"
echo ""

# Build the Docker image
docker build -t "${FULL_IMAGE}" .

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Build successful!${NC}"
    echo ""
else
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

# Ask if user wants to push
read -p "Do you want to push to Docker Hub? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}Logging in to Docker Hub...${NC}"
    docker login
    
    echo ""
    echo -e "${YELLOW}Pushing image: ${FULL_IMAGE}${NC}"
    docker push "${FULL_IMAGE}"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ Push successful!${NC}"
        echo ""
        echo -e "${GREEN}Your image is now available at:${NC}"
        echo -e "${GREEN}  docker pull ${FULL_IMAGE}${NC}"
        echo ""
        echo -e "${YELLOW}Update your docker-compose.yml with:${NC}"
        echo -e "  image: ${FULL_IMAGE}"
    else
        echo -e "${RED}❌ Push failed!${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Done!${NC}"
echo -e "${GREEN}================================================${NC}"

