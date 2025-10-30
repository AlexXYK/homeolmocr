#!/usr/bin/env python3
"""
olmOCR API Service - VLLM Edition
A FastAPI service using VLLM for efficient inference with olmOCR-2-7B-1025-FP8
"""

import os
import base64
import logging
import traceback
import subprocess
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import AsyncOpenAI
from pdf2image import convert_from_bytes

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

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
            "ocr": "/ocr (POST with image file)",
            "metrics": "/metrics"
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


@app.get("/metrics")
async def metrics():
    """Minimal service metrics for observability"""
    try:
        models = await vllm_client.models.list()
        vllm_connected = True
        vllm_error = None
    except Exception as e:
        vllm_connected = False
        vllm_error = str(e)
    
    return {
        "service": "olmOCR API (VLLM-Powered)",
        "version": "2.0.0",
        "model": MODEL_NAME,
        "vllm_url": VLLM_BASE_URL,
        "vllm_connected": vllm_connected,
        "vllm_error": vllm_error,
    }


@app.post("/ocr", response_model=OCRResponse)
async def process_ocr(
    file: UploadFile = File(...),
    convert_html_tables: bool = False,
    pdf_dpi: int = 200,
    max_pages: Optional[int] = None,
    page_separator: str = "---",
):
    """
    Process an image/PDF file and return extracted text in markdown format
    
    Args:
        file: Image/PDF file
        convert_html_tables: Convert HTML tables to Markdown via pandoc
        pdf_dpi: DPI for PDF rendering (default 200)
        max_pages: Maximum pages to process from PDF
        page_separator: Separator between PDF pages (default "---")
        
    Returns:
        OCRResponse with extracted text or error
    """
    try:
        # Helper to OCR a single image
        async def ocr_single_image(pil_image: Image.Image) -> str:
            resized = resize_image_to_target_dim(pil_image, TARGET_IMAGE_DIM)
            image_b64 = image_to_base64(resized)
            prompt_text = build_prompt()
            
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
            return response.choices[0].message.content
        
        # Read file
        logger.info(f"Processing file: {file.filename}")
        contents = await file.read()
        
        # Branch: PDF vs image
        is_pdf = (file.content_type == "application/pdf") or (file.filename and file.filename.lower().endswith(".pdf"))
        
        if is_pdf:
            logger.info("Detected PDF. Converting to images...")
            pages = convert_from_bytes(contents, dpi=pdf_dpi)
            if max_pages is not None:
                pages = pages[:max_pages]
            if not pages:
                return OCRResponse(success=False, error="PDF contained no pages")
            
            page_texts = []
            for idx, page in enumerate(pages):
                if page.mode != 'RGB':
                    page = page.convert('RGB')
                logger.info(f"OCR page {idx+1}/{len(pages)}")
                page_texts.append(await ocr_single_image(page))
            text_output = f"\n\n{page_separator}\n\n".join(page_texts)
            original_size = None
            processed_size = None
        else:
            try:
                image = Image.open(BytesIO(contents))
                if image.mode != 'RGB':
                    image = image.convert('RGB')
            except Exception as e:
                logger.error(f"Failed to open image: {str(e)}")
                return OCRResponse(
                    success=False,
                    error=f"Invalid image file: {str(e)}"
                )
            original_size = image.size
            text_output = await ocr_single_image(image)
            processed_size = resize_image_to_target_dim(image, TARGET_IMAGE_DIM).size
        
        # Optionally convert HTML tables to Markdown using two-stage pandoc pipeline
        if convert_html_tables:
            lower_out = text_output.lower()
            has_table_like = any(tag in lower_out for tag in ["<table", "</table>", "<tr", "<td", "<th"])
            logger.info(f"convert_html_tables={convert_html_tables}, has_table_like={has_table_like}")
            if has_table_like:
                try:
                    logger.info("Converting embedded HTML tables to Markdown via two-stage pandoc...")
                    # Stage 1: Parse mixed markdown+HTML as GFM with raw_html extension → HTML
                    stage1 = subprocess.run(
                        ["pandoc", "-f", "gfm+raw_html", "-t", "html"],
                        input=text_output,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    if stage1.returncode != 0:
                        logger.error(f"Stage 1 pandoc failed: {stage1.stderr}")
                        raise Exception(f"Stage 1 failed: {stage1.stderr}")
                    logger.info("Stage 1 complete")
                    # Stage 2: Convert HTML back to GFM with proper pipe tables
                    stage2 = subprocess.run(
                        ["pandoc", "-f", "html", "-t", "gfm-tex_math_dollars", "--wrap=none"],
                        input=stage1.stdout,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    if stage2.returncode != 0:
                        logger.error(f"Stage 2 pandoc failed: {stage2.stderr}")
                        raise Exception(f"Stage 2 failed: {stage2.stderr}")
                    logger.info("Stage 2 complete")
                    if stage2.stdout.strip():
                        text_output = stage2.stdout
                        logger.info("Successfully converted HTML tables to clean Markdown")
                    else:
                        logger.warning("Pandoc returned empty output, keeping original")
                except Exception as e:
                    logger.error(f"Pandoc two-stage conversion failed: {str(e)}", exc_info=True)
        
        logger.info("OCR processing completed successfully")
        
        return OCRResponse(
            success=True,
            text=text_output,
            metadata={
                "original_size": list(original_size) if original_size else None,
                "processed_size": list(processed_size) if processed_size else None,
                "filename": file.filename,
                "model": MODEL_NAME,
                "engine": "vllm",
                "is_pdf": bool(is_pdf),
                "html_tables_converted": bool(convert_html_tables),
                "page_separator": page_separator if is_pdf else None,
                "pdf_dpi": pdf_dpi if is_pdf else None,
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

