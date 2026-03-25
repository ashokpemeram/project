import importlib
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

import torch
import torch.nn as nn

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from config import (
    ALLOW_PLACEHOLDER_MODEL,
    DEVICE,
    MODEL_CLASS_PATH,
    MODEL_PATH,
    MODEL_STRICT,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelService:
    """Singleton service for PyTorch model management."""

    _instance: Optional["ModelService"] = None
    _model: Optional[nn.Module] = None
    _device: str = "cpu"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            self.load_model()

    def _resolve_model_class(self) -> type[nn.Module]:
        if ":" not in MODEL_CLASS_PATH:
            raise RuntimeError(
                "MODEL_CLASS_PATH must look like 'module.submodule:ClassName'. "
                f"Got: {MODEL_CLASS_PATH}"
            )
        module_path, class_name = MODEL_CLASS_PATH.split(":", 1)
        module = importlib.import_module(module_path)
        model_cls = getattr(module, class_name, None)
        if model_cls is None:
            raise RuntimeError(
                f"Model class '{class_name}' not found in '{module_path}'. "
                "Update MODEL_CLASS_PATH or define the class."
            )
        if not issubclass(model_cls, nn.Module):
            raise RuntimeError(f"{MODEL_CLASS_PATH} is not a torch.nn.Module.")
        return model_cls

    def _create_placeholder_model(self) -> nn.Module:
        class IdentityModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.conv = nn.Conv2d(3, 3, kernel_size=3, padding=1)

            def forward(self, x):
                return torch.sigmoid(self.conv(x))

        return IdentityModel()

    def _load_state_dict(self, model: nn.Module, checkpoint: object) -> Tuple[nn.Module, str]:
        if isinstance(checkpoint, nn.Module):
            return checkpoint, "checkpoint is a full torch.nn.Module"

        if isinstance(checkpoint, dict):
            if "generator_state_dict" in checkpoint:
                state_dict = checkpoint["generator_state_dict"]
            elif "model_state_dict" in checkpoint:
                state_dict = checkpoint["model_state_dict"]
            elif "state_dict" in checkpoint:
                state_dict = checkpoint["state_dict"]
            else:
                state_dict = checkpoint
        else:
            raise RuntimeError("Unsupported checkpoint format. Expected dict or torch.nn.Module.")

        if MODEL_STRICT:
            model.load_state_dict(state_dict, strict=True)
            return model, "state_dict loaded with strict=True"

        incompatible = model.load_state_dict(state_dict, strict=False)
        missing = list(incompatible.missing_keys)
        unexpected = list(incompatible.unexpected_keys)
        msg = "state_dict loaded with strict=False"
        if missing or unexpected:
            msg += f" (missing={len(missing)}, unexpected={len(unexpected)})"
            logger.warning("Missing keys: %s", missing)
            logger.warning("Unexpected keys: %s", unexpected)
        return model, msg

    def load_model(self) -> None:
        try:
            if DEVICE == "cuda" and torch.cuda.is_available():
                self._device = "cuda"
                logger.info("Using GPU: %s", torch.cuda.get_device_name(0))
            else:
                self._device = "cpu"
                logger.info("Using CPU")

            model_path = Path(MODEL_PATH)
            if not model_path.exists():
                msg = f"Model file not found at {MODEL_PATH}"
                if ALLOW_PLACEHOLDER_MODEL:
                    logger.warning("%s. Using placeholder model.", msg)
                    self._model = self._create_placeholder_model()
                    self._model.to(self._device).eval()
                    return
                raise RuntimeError(msg)

            model_cls = self._resolve_model_class()
            model = model_cls()

            logger.info("Loading model weights from %s", MODEL_PATH)
            checkpoint = torch.load(MODEL_PATH, map_location=self._device)
            model, summary = self._load_state_dict(model, checkpoint)

            self._model = model.to(self._device).eval()
            logger.info("Model loaded successfully (%s)", summary)

        except Exception as exc:
            logger.error("Error loading model: %s", exc, exc_info=True)
            if ALLOW_PLACEHOLDER_MODEL:
                logger.warning("Falling back to placeholder model.")
                self._model = self._create_placeholder_model().to(self._device).eval()
                return
            raise

    @torch.no_grad()
    def predict(self, input_tensor: torch.Tensor) -> torch.Tensor:
        if self._model is None:
            raise RuntimeError("Model not loaded")
        input_tensor = input_tensor.to(self._device)
        return self._model(input_tensor)

    def get_device(self) -> str:
        return self._device

    def is_loaded(self) -> bool:
        return self._model is not None


model_service = ModelService()
