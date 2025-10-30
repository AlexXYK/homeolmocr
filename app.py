#!/usr/bin/env python3
"""
olmOCR API Service
A FastAPI service for processing images/PDFs with olmOCR-2-7B-1025-FP8 model
"""

import os
import base64
import logging
import traceback
from io import BytesIO
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

import torch
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import subprocess
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
from pdf2image import convert_from_bytes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global model and processor variables
model = None
processor = None
device = None

# Model configuration
MODEL_NAME = os.getenv("MODEL_NAME", "allenai/olmOCR-2-7B-1025-FP8")
PROCESSOR_NAME = os.getenv("PROCESSOR_NAME", "Qwen/Qwen2.5-VL-7B-Instruct")
TARGET_IMAGE_DIM = int(os.getenv("TARGET_IMAGE_DIM", "1288"))


class OCRResponse(BaseModel):
    """Response model for OCR requests"""
    success: bool
    text: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[dict] = None


def build_prompt() -> str:
    """
    Build the prompt for the olmOCR model
    This is a simplified version of the no_anchoring_v4_yaml_prompt
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


def load_model_on_startup():
    """Load the model and processor on startup"""
    global model, processor, device
    
    try:
        logger.info("Loading olmOCR model and processor...")
        
        # Set CUDA memory management for better fragmentation handling
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
        
        # Determine device
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {device}")
        
        # Load processor
        logger.info(f"Loading processor from {PROCESSOR_NAME}")
        processor = AutoProcessor.from_pretrained(PROCESSOR_NAME)
        
        # Load model
        logger.info(f"Loading model from {MODEL_NAME}")
        model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.bfloat16,
            device_map="auto" if torch.cuda.is_available() else None
        ).eval()
        
        if not torch.cuda.is_available():
            model.to(device)
        
        # Clear any cached memory
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Model and processor loaded successfully!")
        
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        logger.error(traceback.format_exc())
        raise


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load model
    load_model_on_startup()
    yield
    # Shutdown (cleanup if needed)
    pass


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="olmOCR API",
    description="OCR service using olmOCR-2-7B-1025-FP8 for converting images to markdown",
    version="1.0.0",
    lifespan=lifespan
)

# Enable permissive CORS by default to simplify integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "olmOCR API",
        "version": "1.0.0",
        "model": MODEL_NAME,
        "status": "ready" if model is not None else "loading",
        "device": str(device) if device else "unknown",
        "endpoints": {
            "health": "/health",
            "ocr": "/ocr (POST with image file)",
            "metrics": "/metrics"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if model is not None else "initializing",
        "model_loaded": model is not None,
        "device": str(device) if device else "unknown",
        "cuda_available": torch.cuda.is_available()
    }


@app.get("/metrics")
async def metrics():
    """Minimal service metrics for observability and readiness checks"""
    cuda_available = torch.cuda.is_available()
    cuda = None
    if cuda_available:
        try:
            current_device = torch.cuda.current_device()
            cuda = {
                "device_index": int(current_device),
                "device_name": torch.cuda.get_device_name(current_device),
                # Values in bytes to avoid units ambiguity
                "memory_allocated": int(torch.cuda.memory_allocated(current_device)),
                "memory_reserved": int(torch.cuda.memory_reserved(current_device)),
            }
        except Exception:
            cuda = {"error": "unable to query cuda stats"}

    return {
        "service": "olmOCR API",
        "version": "1.0.0",
        "model": MODEL_NAME,
        "model_loaded": model is not None,
        "device": str(device) if device else "unknown",
        "cuda_available": cuda_available,
        "cuda": cuda,
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
    Process an image file and return extracted text in markdown format
    
    Args:
        file: Image file (JPEG, PNG, etc.)
        
    Returns:
        OCRResponse with extracted text or error
    """
    if model is None or processor is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")
    
    try:
        # Helper to OCR a single PIL image
        def ocr_image_to_text(pil_image: Image.Image) -> str:
            resized = resize_image_to_target_dim(pil_image, TARGET_IMAGE_DIM)
            prompt_text = build_prompt()
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image", "image": resized},
                    ],
                }
            ]
            templated = processor.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            inputs = processor(
                text=[templated],
                images=[resized],
                padding=True,
                return_tensors="pt",
            )
            inputs = {key: value.to(device) for key, value in inputs.items()}
            with torch.no_grad():
                output = model.generate(
                    **inputs,
                    temperature=0.1,
                    max_new_tokens=4096,
                    num_return_sequences=1,
                    do_sample=True,
                )
            prompt_length = inputs["input_ids"].shape[1]
            new_tokens = output[:, prompt_length:]
            page_text = processor.tokenizer.batch_decode(
                new_tokens,
                skip_special_tokens=True,
            )[0]
            return page_text

        logger.info(f"Processing file: {file.filename}")
        contents = await file.read()

        # Branch: PDF vs image
        is_pdf = (file.content_type == "application/pdf") or (file.filename and file.filename.lower().endswith(".pdf"))

        if is_pdf:
            logger.info("Detected PDF. Converting to images...")
            pages: list[Image.Image] = convert_from_bytes(contents, dpi=pdf_dpi)
            if max_pages is not None:
                pages = pages[:max_pages]
            if not pages:
                return OCRResponse(success=False, error="PDF contained no pages")
            page_texts = []
            for idx, page in enumerate(pages):
                if page.mode != 'RGB':
                    page = page.convert('RGB')
                logger.info(f"OCR page {idx+1}/{len(pages)}")
                page_texts.append(ocr_image_to_text(page))
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
            text_output = ocr_image_to_text(image)
            processed_size = resize_image_to_target_dim(image, TARGET_IMAGE_DIM).size

        # Optionally convert HTML tables to Markdown using two-stage pandoc pipeline
        # Stage 1: gfm+raw_html → html  | Stage 2: html → gfm-tex_math_dollars
        if convert_html_tables:
            lower_out = text_output.lower()
            has_table_like = any(tag in lower_out for tag in ["<table", "</table>", "<tr", "<td", "<th"])            
            if has_table_like:
                try:
                    logger.info("Converting embedded HTML tables to Markdown via two-stage pandoc...")
                    # Stage 1: Parse mixed markdown+HTML as GFM with raw_html extension → HTML
                    stage1 = subprocess.run(
                        ["pandoc", "-f", "gfm+raw_html", "-t", "html"],
                        input=text_output,
                        text=True,
                        capture_output=True,
                        check=True,
                    )
                    # Stage 2: Convert HTML back to GFM with proper pipe tables
                    stage2 = subprocess.run(
                        ["pandoc", "-f", "html", "-t", "gfm-tex_math_dollars", "--wrap=none"],
                        input=stage1.stdout,
                        text=True,
                        capture_output=True,
                        check=True,
                    )
                    if stage2.stdout.strip():
                        text_output = stage2.stdout
                        logger.info("Successfully converted HTML tables to clean Markdown")
                except Exception as e:
                    logger.warning(f"Pandoc two-stage conversion failed: {str(e)}")

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info("OCR processing completed successfully")

        return OCRResponse(
            success=True,
            text=text_output,
            metadata={
                "original_size": original_size,
                "processed_size": processed_size,
                "filename": file.filename,
                "model": MODEL_NAME,
                "html_tables_converted": bool(convert_html_tables),
                "is_pdf": bool(is_pdf),
                "page_separator": page_separator if is_pdf else None,
                "pdf_dpi": pdf_dpi if is_pdf else None,
                "page_count": text_output.count(f"\n\n{page_separator}\n\n") + 1 if is_pdf else None,
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
    port = int(os.getenv("PORT", "5005"))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

