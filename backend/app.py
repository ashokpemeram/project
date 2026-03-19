from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
import base64
import logging
from datetime import datetime
import uuid
from pathlib import Path
from contextlib import asynccontextmanager
import torch

from attack_metrics import compute_mse, compute_psnr
from attacker import Attacker, build_default_training_attacker
from model_service import model_service
from utils import (
    validate_image,
    preprocess_image,
    postprocess_output,
    output_to_unit_interval,
    rgb_to_grayscale_minus1_1,
    grayscale_minus1_1_to_png_bytes,
    grayscale_unit_interval_to_png_bytes,
)
from config import API_PREFIX, CORS_ORIGINS, UPLOAD_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _build_attacker(attack_type: str, device: str) -> torch.nn.Module:
    attack_type = (attack_type or "combined").strip().lower()
    if attack_type == "combined":
        attacker = build_default_training_attacker()
    else:
        attacker = Attacker(attack_type)
    return attacker.to(device).eval()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting Medical Image Protection API")
    if model_service.is_loaded():
        logger.info(f"Model loaded successfully on {model_service.get_device()}")
    else:
        logger.warning("Model not loaded - check configuration")
    yield
    # Shutdown (optional cleanup code here)


# Initialize FastAPI app
app = FastAPI(
    title="Medical Image Protection API",
    description="API for processing medical images using PyTorch model",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Medical Image Protection API",
        "status": "running",
        "model_loaded": model_service.is_loaded(),
        "device": model_service.get_device()
    }


@app.get(f"{API_PREFIX}/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model_service.is_loaded(),
        "device": model_service.get_device(),
        "timestamp": datetime.now().isoformat()
    }


@app.post(f"{API_PREFIX}/protect-image")
async def protect_image(image: UploadFile = File(...)):
    """
    Process uploaded image using PyTorch model
    
    Args:
        image: Uploaded image file
        
    Returns:
        Protected/secured image
    """
    try:
        # Read file content
        logger.info(f"Processing image: {image.filename}")
        file_content = await image.read()
        
        # Validate image
        is_valid, error_msg = validate_image(file_content, image.filename)
        if not is_valid:
            logger.warning(f"Validation failed: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Preprocess image
        logger.info("Preprocessing image")
        input_tensor = preprocess_image(file_content, model_service.get_device())
        
        # Run inference
        logger.info("Running model inference")
        output_tensor = model_service.predict(input_tensor)
        
        # Postprocess output
        logger.info("Postprocessing output")
        output_bytes = postprocess_output(output_tensor)
        
        logger.info("Image processed successfully")
        
        # Return image as response
        return Response(
            content=output_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=protected_{uuid.uuid4().hex[:8]}.png"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )


@app.post(f"{API_PREFIX}/protect-image-json")
async def protect_image_json(image: UploadFile = File(...)):
    """
    Alternative endpoint that returns JSON with base64 image
    Useful for debugging or different frontend requirements
    """
    import base64
    
    try:
        file_content = await image.read()
        
        # Validate
        is_valid, error_msg = validate_image(file_content, image.filename)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": error_msg}
            )
        
        # Process
        input_tensor = preprocess_image(file_content, model_service.get_device())
        output_tensor = model_service.predict(input_tensor)
        output_bytes = postprocess_output(output_tensor)
        
        # Encode to base64
        img_base64 = base64.b64encode(output_bytes).decode('utf-8')
        
        return {
            "success": True,
            "message": "Image processed successfully",
            "image": f"data:image/png;base64,{img_base64}"
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post(f"{API_PREFIX}/protect-image-attack")
async def protect_image_attack(
    image: UploadFile = File(...),
    attack_type: str = Form("combined"),
    tamper_threshold: float = Form(0.25),
):
    """
    Process uploaded image and run an attacker simulation on the protected output.

    Returns JSON with base64-encoded protected + attacked images and attack metrics.
    """
    try:
        file_content = await image.read()

        # Validate
        is_valid, error_msg = validate_image(file_content, image.filename)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": error_msg}
            )

        # Protect image
        input_tensor = preprocess_image(file_content, model_service.get_device())
        protected_tensor = model_service.predict(input_tensor)

        # Convert tensors to [0, 1] for metrics and to grayscale [-1, 1] for attacker
        original_unit = output_to_unit_interval(input_tensor)
        protected_unit = output_to_unit_interval(protected_tensor)
        protected_gray = rgb_to_grayscale_minus1_1(protected_unit)

        # Run attacker
        attacker = _build_attacker(attack_type, model_service.get_device())
        with torch.no_grad():
            attacked_gray = attacker(protected_gray)

        # Compute metrics
        attack_distance = (attacked_gray - protected_gray).abs().mean().item()
        original_m11 = original_unit * 2.0 - 1.0
        protected_m11 = protected_unit * 2.0 - 1.0

        metrics = {
            "attack_distance": attack_distance,
            "mse_attacked_vs_protected": compute_mse(attacked_gray, protected_gray).item(),
            "psnr_attacked_vs_protected": compute_psnr(attacked_gray, protected_gray).item(),
            "mse_protected_vs_original": compute_mse(protected_m11, original_m11).item(),
            "psnr_protected_vs_original": compute_psnr(protected_m11, original_m11).item(),
        }

        # Tamper maps (attacked vs protected)
        tamper_map = (attacked_gray - protected_gray).abs()
        tamper_map_norm = tamper_map / tamper_map.amax(dim=(2, 3), keepdim=True).clamp_min(1e-8)
        threshold = max(0.0, min(1.0, float(tamper_threshold)))
        tamper_mask = (tamper_map_norm > threshold).to(tamper_map_norm.dtype)

        # Convert outputs to PNG bytes
        protected_bytes = postprocess_output(protected_tensor)
        attacked_bytes = grayscale_minus1_1_to_png_bytes(attacked_gray)
        tamper_map_bytes = grayscale_unit_interval_to_png_bytes(tamper_map_norm)
        tamper_mask_bytes = grayscale_unit_interval_to_png_bytes(tamper_mask)

        protected_b64 = base64.b64encode(protected_bytes).decode("utf-8")
        attacked_b64 = base64.b64encode(attacked_bytes).decode("utf-8")
        tamper_map_b64 = base64.b64encode(tamper_map_bytes).decode("utf-8")
        tamper_mask_b64 = base64.b64encode(tamper_mask_bytes).decode("utf-8")

        return {
            "success": True,
            "attack_type": attack_type,
            "protected_image": f"data:image/png;base64,{protected_b64}",
            "attacked_image": f"data:image/png;base64,{attacked_b64}",
            "tamper_map": f"data:image/png;base64,{tamper_map_b64}",
            "tamper_mask": f"data:image/png;base64,{tamper_mask_b64}",
            "tamper_threshold": threshold,
            "metrics": metrics,
        }

    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"Attack error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )
