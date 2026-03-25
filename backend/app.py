import base64
import logging
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import torch
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.encoders import ENCODERS_BY_TYPE
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure ObjectId values from Mongo can be serialized in any response payload.
try:
    from bson import ObjectId

    ENCODERS_BY_TYPE[ObjectId] = str
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from attacker.attack_metrics import compute_mse, compute_psnr, compute_ssim
from attacker.attacker import Attacker, build_default_training_attacker
from config import API_PREFIX, CORS_ORIGINS, PROTECTED_DIR, STORE_PATH
from model_service import model_service
from repository import get_store
from security import hash_password, new_token, verify_password
from utils import (
    grayscale_minus1_1_to_png_bytes,
    grayscale_unit_interval_to_png_bytes,
    load_image_unit_tensor,
    output_to_unit_interval,
    postprocess_output,
    preprocess_image,
    rgb_to_grayscale_minus1_1,
    validate_image,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

store = get_store()


def _build_attacker(attack_type: str, device: str) -> torch.nn.Module:
    attack_type = (attack_type or "combined").strip().lower()
    if attack_type == "combined":
        attacker = build_default_training_attacker()
    else:
        attacker = Attacker(attack_type)
    return attacker.to(device).eval()


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _sanitize_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role", "doctor"),
    }


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1].strip()
    user = store.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return user


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AttackRequest(BaseModel):
    patient_id: str
    attack_type: str = "combined"
    tamper_threshold: float = 0.25


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Secure Hospital Imaging API")
    if model_service.is_loaded():
        logger.info("Model loaded successfully on %s", model_service.get_device())
    else:
        logger.warning("Model not loaded - check configuration")
    yield


app = FastAPI(
    title="Secure Hospital Imaging API",
    description="API for protecting and analyzing medical images",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/protected", StaticFiles(directory=str(PROTECTED_DIR)), name="protected")


@app.get("/")
async def root():
    return {
        "message": "Secure Hospital Imaging API",
        "status": "running",
        "model_loaded": model_service.is_loaded(),
        "device": model_service.get_device(),
    }


@app.get(f"{API_PREFIX}/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model_service.is_loaded(),
        "device": model_service.get_device(),
        "timestamp": _now_iso(),
    }


@app.post(f"{API_PREFIX}/auth/signup")
async def signup(payload: SignupRequest):
    try:
        password_hash = hash_password(payload.password)
        user = store.create_user(payload.name, payload.email, password_hash)
        token = new_token()
        store.create_session(user["id"], token)
        return {"success": True, "token": token, "user": _sanitize_user(user)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post(f"{API_PREFIX}/auth/login")
async def login(payload: LoginRequest):
    user = store.get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = new_token()
    store.create_session(user["id"], token)
    return {"success": True, "token": token, "user": _sanitize_user(user)}


@app.post(f"{API_PREFIX}/upload")
async def upload_patient_scan(
    image: UploadFile = File(...),
    patient_name: str = Form(...),
    patient_id: str = Form(...),
    scan_type: str = Form(...),
    diagnosis_notes: str = Form(""),
    user: dict = Depends(get_current_user),
):
    try:
        file_content = await image.read()
        is_valid, error_msg = validate_image(file_content, image.filename)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        input_tensor = preprocess_image(file_content, model_service.get_device())
        protected_tensor = model_service.predict(input_tensor)

        original_unit = output_to_unit_interval(input_tensor)
        protected_unit = output_to_unit_interval(protected_tensor)
        original_m11 = original_unit * 2.0 - 1.0
        protected_m11 = protected_unit * 2.0 - 1.0

        protection_metrics = {
            "mse_protected_vs_original": compute_mse(protected_m11, original_m11).item(),
            "psnr_protected_vs_original": compute_psnr(protected_m11, original_m11).item(),
            "ssim_protected_vs_original": compute_ssim(protected_m11, original_m11).item(),
        }

        protected_bytes = postprocess_output(protected_tensor)
        filename = f"{uuid.uuid4().hex}.png"
        output_path = PROTECTED_DIR / filename
        output_path.write_bytes(protected_bytes)

        patient_record = {
            "id": uuid.uuid4().hex,
            "patient_name": patient_name.strip(),
            "patient_id": patient_id.strip(),
            "scan_type": scan_type.strip(),
            "diagnosis_notes": diagnosis_notes.strip(),
            "protected_filename": filename,
            "protected_url": f"/protected/{filename}",
            "status": "Protected",
            "created_at": _now_iso(),
            "created_by": user["id"],
            "protection_metrics": protection_metrics,
        }

        patient_record = store.add_patient(patient_record)

        return {"success": True, "patient": patient_record}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Upload error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}")


@app.get(f"{API_PREFIX}/patients")
async def list_patients(user: dict = Depends(get_current_user)):
    patients = store.list_patients()
    patients = sorted(patients, key=lambda p: p.get("created_at", ""), reverse=True)
    return {"success": True, "patients": patients}


@app.get(f"{API_PREFIX}/patients/{{patient_id}}")
async def get_patient(patient_id: str, user: dict = Depends(get_current_user)):
    patient = store.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    attacks = store.list_attacks_for_patient(patient_id)
    return {"success": True, "patient": patient, "attacks": attacks}


@app.post(f"{API_PREFIX}/attack")
async def run_attack(payload: AttackRequest, user: dict = Depends(get_current_user)):
    patient = store.get_patient(payload.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    file_path = PROTECTED_DIR / patient["protected_filename"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Protected image not found")

    protected_bytes = file_path.read_bytes()
    protected_unit = load_image_unit_tensor(protected_bytes, model_service.get_device())
    protected_gray = rgb_to_grayscale_minus1_1(protected_unit)

    try:
        attacker = _build_attacker(payload.attack_type, model_service.get_device())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    with torch.no_grad():
        attacked_gray = attacker(protected_gray)

    tamper_map = (attacked_gray - protected_gray).abs()
    tamper_map_norm = tamper_map / tamper_map.amax(dim=(2, 3), keepdim=True).clamp_min(1e-8)
    threshold = max(0.0, min(1.0, float(payload.tamper_threshold)))
    tamper_mask = (tamper_map_norm > threshold).to(tamper_map_norm.dtype)

    metrics = {
        "mse_attacked_vs_protected": compute_mse(attacked_gray, protected_gray).item(),
        "psnr_attacked_vs_protected": compute_psnr(attacked_gray, protected_gray).item(),
        "ssim_attacked_vs_protected": compute_ssim(attacked_gray, protected_gray).item(),
    }

    attacked_bytes = grayscale_minus1_1_to_png_bytes(attacked_gray)
    tamper_map_bytes = grayscale_unit_interval_to_png_bytes(tamper_map_norm)
    tamper_mask_bytes = grayscale_unit_interval_to_png_bytes(tamper_mask)

    attacked_b64 = base64.b64encode(attacked_bytes).decode("utf-8")
    tamper_map_b64 = base64.b64encode(tamper_map_bytes).decode("utf-8")
    tamper_mask_b64 = base64.b64encode(tamper_mask_bytes).decode("utf-8")

    attack_record = {
        "id": uuid.uuid4().hex,
        "patient_id": patient["id"],
        "attack_type": payload.attack_type,
        "tamper_threshold": threshold,
        "metrics": metrics,
        "created_at": _now_iso(),
    }
    store.add_attack(attack_record)
    store.update_patient(
        patient["id"],
        {
            "status": "Attacked",
            "last_attack_at": attack_record["created_at"],
            "last_attack_type": payload.attack_type,
        },
    )

    return {
        "success": True,
        "attack_type": payload.attack_type,
        "protected_image_url": patient["protected_url"],
        "attacked_image": f"data:image/png;base64,{attacked_b64}",
        "tamper_map": f"data:image/png;base64,{tamper_map_b64}",
        "tamper_mask": f"data:image/png;base64,{tamper_mask_b64}",
        "tamper_threshold": threshold,
        "metrics": metrics,
    }


@app.post(f"{API_PREFIX}/protect-image")
async def protect_image(image: UploadFile = File(...)):
    try:
        logger.info("Processing image: %s", image.filename)
        file_content = await image.read()

        is_valid, error_msg = validate_image(file_content, image.filename)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        input_tensor = preprocess_image(file_content, model_service.get_device())
        output_tensor = model_service.predict(input_tensor)
        output_bytes = postprocess_output(output_tensor)

        return Response(
            content=output_bytes,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=protected_{uuid.uuid4().hex[:8]}.png"},
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error processing image: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing image: {exc}")


@app.post(f"{API_PREFIX}/protect-image-json")
async def protect_image_json(image: UploadFile = File(...)):
    try:
        file_content = await image.read()

        is_valid, error_msg = validate_image(file_content, image.filename)
        if not is_valid:
            return JSONResponse(status_code=400, content={"success": False, "error": error_msg})

        input_tensor = preprocess_image(file_content, model_service.get_device())
        output_tensor = model_service.predict(input_tensor)
        output_bytes = postprocess_output(output_tensor)

        img_base64 = base64.b64encode(output_bytes).decode("utf-8")
        return {
            "success": True,
            "message": "Image processed successfully",
            "image": f"data:image/png;base64,{img_base64}",
        }

    except Exception as exc:
        logger.error("Error: %s", exc)
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})


@app.post(f"{API_PREFIX}/protect-image-attack")
async def protect_image_attack(
    image: UploadFile = File(...),
    attack_type: str = Form("combined"),
    tamper_threshold: float = Form(0.25),
):
    try:
        file_content = await image.read()

        is_valid, error_msg = validate_image(file_content, image.filename)
        if not is_valid:
            return JSONResponse(status_code=400, content={"success": False, "error": error_msg})

        input_tensor = preprocess_image(file_content, model_service.get_device())
        protected_tensor = model_service.predict(input_tensor)

        original_unit = output_to_unit_interval(input_tensor)
        protected_unit = output_to_unit_interval(protected_tensor)
        protected_gray = rgb_to_grayscale_minus1_1(protected_unit)

        attacker = _build_attacker(attack_type, model_service.get_device())
        with torch.no_grad():
            attacked_gray = attacker(protected_gray)

        attack_distance = (attacked_gray - protected_gray).abs().mean().item()
        original_m11 = original_unit * 2.0 - 1.0
        protected_m11 = protected_unit * 2.0 - 1.0

        metrics = {
            "attack_distance": attack_distance,
            "mse_attacked_vs_protected": compute_mse(attacked_gray, protected_gray).item(),
            "psnr_attacked_vs_protected": compute_psnr(attacked_gray, protected_gray).item(),
            "ssim_attacked_vs_protected": compute_ssim(attacked_gray, protected_gray).item(),
            "mse_protected_vs_original": compute_mse(protected_m11, original_m11).item(),
            "psnr_protected_vs_original": compute_psnr(protected_m11, original_m11).item(),
            "ssim_protected_vs_original": compute_ssim(protected_m11, original_m11).item(),
        }

        tamper_map = (attacked_gray - protected_gray).abs()
        tamper_map_norm = tamper_map / tamper_map.amax(dim=(2, 3), keepdim=True).clamp_min(1e-8)
        threshold = max(0.0, min(1.0, float(tamper_threshold)))
        tamper_mask = (tamper_map_norm > threshold).to(tamper_map_norm.dtype)

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

    except ValueError as exc:
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})
    except Exception as exc:
        logger.error("Attack error: %s", exc, exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info",
    )
