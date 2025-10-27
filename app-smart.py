#!/usr/bin/env python3
"""
olmOCR API Service - Smart Memory Management Edition
Loads model on-demand and unloads after inactivity
Perfect for sharing GPU with Ollama!
"""

import os
import logging
import traceback
import asyncio
from io import BytesIO
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import torch
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
MODEL_NAME = os.getenv("MODEL_NAME", "allenai/olmOCR-2-7B-1025-FP8")
PROCESSOR_NAME = os.getenv("PROCESSOR_NAME", "Qwen/Qwen2.5-VL-7B-Instruct")
TARGET_IMAGE_DIM = int(os.getenv("TARGET_IMAGE_DIM", "1024"))
KEEP_ALIVE_SECONDS = int(os.getenv("KEEP_ALIVE_SECONDS", "300"))  # 5 minutes default
API_PORT = int(os.getenv("PORT", "5005"))

# Global model state
model = None
processor = None
device = None
last_used_time = None
unload_task = None
model_lock = asyncio.Lock()


class OCRResponse(BaseModel):
    """Response model for OCR requests"""
    success: bool
    text: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[dict] = None


class StatusResponse(BaseModel):
    """Status response"""
    status: str
    model_loaded: bool
    gpu_available: bool
    keep_alive_seconds: int
    time_until_unload: Optional[int] = None


def build_prompt() -> str:
    """Build the prompt for the olmOCR model"""
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
    """Resize image so the longest dimension is target_dim pixels"""
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


async def unload_model_after_delay():
    """Unload model after KEEP_ALIVE_SECONDS of inactivity"""
    global model, processor, last_used_time, unload_task
    
    while True:
        await asyncio.sleep(10)  # Check every 10 seconds
        
        if model is None or last_used_time is None:
            continue
        
        time_since_use = (datetime.now() - last_used_time).total_seconds()
        
        if time_since_use >= KEEP_ALIVE_SECONDS:
            logger.info(f"Model inactive for {KEEP_ALIVE_SECONDS}s, unloading to free GPU memory...")
            async with model_lock:
                if model is not None:
                    del model
                    del processor
                    model = None
                    processor = None
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    logger.info("✅ Model unloaded. GPU memory freed for other tasks!")


def load_model():
    """Load the model and processor"""
    global model, processor, device
    
    if model is not None:
        logger.info("Model already loaded, skipping...")
        return
    
    try:
        logger.info("🔄 Loading olmOCR model (this takes 30-60 seconds)...")
        
        # Set CUDA memory management
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
        
        logger.info("✅ Model loaded successfully! Ready for OCR.")
        
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        logger.error(traceback.format_exc())
        raise


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    global device, unload_task
    
    # Startup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"🚀 olmOCR API starting (Smart Memory Mode)")
    logger.info(f"GPU Available: {torch.cuda.is_available()}")
    logger.info(f"Keep-Alive: {KEEP_ALIVE_SECONDS} seconds")
    logger.info(f"Model will load on first request, unload after {KEEP_ALIVE_SECONDS}s of inactivity")
    
    # Start background task to check for model unload
    unload_task = asyncio.create_task(unload_model_after_delay())
    
    yield
    
    # Shutdown
    if unload_task:
        unload_task.cancel()
    logger.info("Shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="olmOCR API (Smart Memory)",
    description="OCR service with intelligent GPU memory management - coexists with Ollama!",
    version="2.1.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "olmOCR API (Smart Memory)",
        "version": "2.1.0",
        "model": MODEL_NAME,
        "mode": "on-demand",
        "keep_alive": f"{KEEP_ALIVE_SECONDS}s",
        "model_loaded": model is not None,
        "gpu_available": torch.cuda.is_available(),
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "ocr": "/ocr (POST with image file)"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "gpu_available": torch.cuda.is_available(),
        "mode": "smart_memory"
    }


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Detailed status including time until unload"""
    global last_used_time
    
    time_until_unload = None
    if model is not None and last_used_time is not None:
        elapsed = (datetime.now() - last_used_time).total_seconds()
        time_until_unload = max(0, int(KEEP_ALIVE_SECONDS - elapsed))
    
    return StatusResponse(
        status="ready" if model is not None else "idle",
        model_loaded=model is not None,
        gpu_available=torch.cuda.is_available(),
        keep_alive_seconds=KEEP_ALIVE_SECONDS,
        time_until_unload=time_until_unload
    )


@app.post("/ocr", response_model=OCRResponse)
async def process_ocr(file: UploadFile = File(...)):
    """
    Process an image file and return extracted text in markdown format
    Model loads on-demand if not already loaded
    """
    global model, processor, last_used_time
    
    try:
        # Load model if needed (thread-safe)
        async with model_lock:
            if model is None:
                logger.info("Model not loaded, loading now...")
                load_model()
        
        # Update last used time (resets unload timer)
        last_used_time = datetime.now()
        
        # Read and validate image
        logger.info(f"Processing file: {file.filename}")
        contents = await file.read()
        
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
        
        # Resize image
        original_size = image.size
        image = resize_image_to_target_dim(image, TARGET_IMAGE_DIM)
        logger.info(f"Image resized from {original_size} to {image.size}")
        
        # Prepare prompt
        prompt_text = build_prompt()
        
        # Build messages
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image", "image": image},
                ],
            }
        ]
        
        # Apply chat template
        text = processor.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        # Process inputs
        inputs = processor(
            text=[text],
            images=[image],
            padding=True,
            return_tensors="pt",
        )
        inputs = {key: value.to(device) for key, value in inputs.items()}
        
        # Generate output
        logger.info("Generating OCR output...")
        with torch.no_grad():
            output = model.generate(
                **inputs,
                temperature=0.1,
                max_new_tokens=4096,
                num_return_sequences=1,
                do_sample=True,
            )
        
        # Decode output
        prompt_length = inputs["input_ids"].shape[1]
        new_tokens = output[:, prompt_length:]
        text_output = processor.tokenizer.batch_decode(
            new_tokens, 
            skip_special_tokens=True
        )[0]
        
        # Clear GPU cache after processing
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Update last used time (extends keep-alive)
        last_used_time = datetime.now()
        
        logger.info(f"✅ OCR completed! Model will stay loaded for {KEEP_ALIVE_SECONDS}s")
        
        return OCRResponse(
            success=True,
            text=text_output,
            metadata={
                "original_size": list(original_size),
                "processed_size": list(image.size),
                "filename": file.filename,
                "model": MODEL_NAME,
                "mode": "smart_memory",
                "model_will_unload_in": f"{KEEP_ALIVE_SECONDS}s"
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
        "app-smart:app",
        host="0.0.0.0",
        port=API_PORT,
        log_level="info"
    )

