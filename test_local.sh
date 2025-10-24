#!/bin/bash
# Local testing script for olmOCR API

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}olmOCR API - Local Test${NC}"
echo -e "${GREEN}================================================${NC}"

# Check if image exists
IMAGE_NAME=${DOCKER_USERNAME:-yourusername}/olmocr-api:latest

echo -e "${YELLOW}Starting container: ${IMAGE_NAME}${NC}"
echo ""

# Run the container
docker run --rm --gpus all -p 5005:5005 \
    -e MODEL_NAME=allenai/olmOCR-2-7B-1025-FP8 \
    -e PROCESSOR_NAME=Qwen/Qwen2.5-VL-7B-Instruct \
    -e TARGET_IMAGE_DIM=1288 \
    "${IMAGE_NAME}"

