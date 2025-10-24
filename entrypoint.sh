#!/bin/bash
set -e

echo "================================================"
echo "olmOCR API Service - Starting"
echo "================================================"
echo "Model: ${MODEL_NAME:-allenai/olmOCR-2-7B-1025-FP8}"
echo "Port: ${PORT:-5005}"
echo "CUDA Available: $(python -c 'import torch; print(torch.cuda.is_available())')"
echo "CUDA Devices: $(python -c 'import torch; print(torch.cuda.device_count())')"
echo "================================================"

# Execute the main command
exec "$@"

