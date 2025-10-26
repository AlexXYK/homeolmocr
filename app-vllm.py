#!/usr/bin/env python3
"""
olmOCR API Service - VLLM Edition
A FastAPI service using VLLM for efficient inference with olmOCR-2-7B-1025-FP8
"""

import os
import base64
import logging
import traceback
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import AsyncOpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "allenai/olmOCR-2-7B-1025-FP8")
TARGET_IMAGE_DIM = int(os.getenv("TARGET_IMAGE_DIM", "1024"))
API_PORT = int(os.getenv("PORT", "5005"))

# Initialize FastAPI app
app = FastAPI(
    title="olmOCR API (VLLM-Powered)",
    description="Efficient OCR service using VLLM for olmOCR-2-7B-1025-FP8",
    version="2.0.0"
)

# OpenAI client for VLLM communication
vllm_client = AsyncOpenAI(
    base_url=VLLM_BASE_URL,
    api_key="EMPTY"  # VLLM doesn't require auth by default
)


class OCRResponse(BaseModel):
    """Response model for OCR requests"""
    success: bool
    text: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[dict] = None


def build_prompt() -> str:
    """
    Build the prompt for the olmOCR model
    """
    prompt = """Extract all text from this image in markdown format. Preserve the structure, formatting, and layout as much as possible. Include:
- All headings and subheadings
- All paragraphs and text blocks
- Any tables (formatted as markdown tables)
- Any lists (formatted as markdown lists)
- Any mathematical equations
- Any special formatting (bold, italic, etc.)

Return only the extracted text in clean markdown format."""
    return prompt


def resize_image_to_target_dim(image: Image.Image, target_dim: int) -> Image.Image:
    """
    Resize image so the longest dimension is target_dim pixels
    
    Args:
        image: PIL Image to resize
        target_dim: Target size for longest dimension
        
    Returns:
        Resized PIL Image
    """
    width, height = image.size
    if max(width, height) <= target_dim:
        return image
    
    if width > height:
        new_width = target_dim
        new_height = int(height * (target_dim / width))
    else:
        new_height = target_dim
        new_width = int(width * (target_dim / height))
    
    return image.resize((new_width, new_height), Image.LANCZOS)


def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string"""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


@app.get("/")
async def root():
    """Root endpoint with API information"""
    # Check VLLM health
    try:
        models = await vllm_client.models.list()
        vllm_status = "connected"
    except Exception as e:
        vllm_status = f"error: {str(e)}"
    
    return {
        "service": "olmOCR API (VLLM-Powered)",
        "version": "2.0.0",
        "model": MODEL_NAME,
        "vllm_status": vllm_status,
        "vllm_url": VLLM_BASE_URL,
        "endpoints": {
            "health": "/health",
            "ocr": "/ocr (POST with image file)"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if VLLM server is responsive
        models = await vllm_client.models.list()
        return {
            "status": "healthy",
            "vllm_connected": True,
            "model": MODEL_NAME,
            "vllm_url": VLLM_BASE_URL
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "vllm_connected": False,
            "error": str(e),
            "vllm_url": VLLM_BASE_URL
        }, 503


@app.post("/ocr", response_model=OCRResponse)
async def process_ocr(file: UploadFile = File(...)):
    """
    Process an image file and return extracted text in markdown format
    
    Args:
        file: Image file (JPEG, PNG, etc.)
        
    Returns:
        OCRResponse with extracted text or error
    """
    try:
        # Read and validate image
        logger.info(f"Processing file: {file.filename}")
        contents = await file.read()
        
        try:
            image = Image.open(BytesIO(contents))
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
        except Exception as e:
            logger.error(f"Failed to open image: {str(e)}")
            return OCRResponse(
                success=False,
                error=f"Invalid image file: {str(e)}"
            )
        
        # Resize image to target dimension
        original_size = image.size
        image = resize_image_to_target_dim(image, TARGET_IMAGE_DIM)
        logger.info(f"Image resized from {original_size} to {image.size}")
        
        # Convert image to base64
        image_b64 = image_to_base64(image)
        
        # Prepare prompt
        prompt_text = build_prompt()
        
        # Call VLLM server using OpenAI-compatible API
        logger.info("Sending request to VLLM server...")
        response = await vllm_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_b64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1,
            max_tokens=4096,
        )
        
        # Extract text from response
        text_output = response.choices[0].message.content
        
        logger.info("OCR processing completed successfully")
        
        return OCRResponse(
            success=True,
            text=text_output,
            metadata={
                "original_size": list(original_size),
                "processed_size": list(image.size),
                "filename": file.filename,
                "model": MODEL_NAME,
                "engine": "vllm"
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing OCR: {str(e)}")
        logger.error(traceback.format_exc())
        return OCRResponse(
            success=False,
            error=f"Processing error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app-vllm:app",
        host="0.0.0.0",
        port=API_PORT,
        log_level="info"
    )

