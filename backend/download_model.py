from __future__ import annotations

import logging
from pathlib import Path

import gdown

logger = logging.getLogger(__name__)


def _is_nonempty_file(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def ensure_model_download(model_path: Path, model_url: str | None) -> Path:
    """Ensure the model exists locally, downloading from Google Drive if needed."""
    model_path = Path(model_path)
    if _is_nonempty_file(model_path):
        logger.info("Model weights already present at %s; skipping download.", model_path)
        return model_path

    if not model_url:
        raise RuntimeError("MODEL_URL is not set and model file is missing.")

    model_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = model_path.with_suffix(model_path.suffix + ".tmp")
    if tmp_path.exists():
        tmp_path.unlink()

    try:
        logger.info("Downloading model weights from %s", model_url)
        download_kwargs = {
            "output": str(tmp_path),
            "quiet": False,
        }
        if "://" not in model_url and "drive.google" not in model_url:
            result = gdown.download(id=model_url, **download_kwargs)
        else:
            result = gdown.download(url=model_url, fuzzy=True, **download_kwargs)

        if not result or not _is_nonempty_file(tmp_path):
            raise RuntimeError("Downloaded file is empty or missing.")

        tmp_path.replace(model_path)
        logger.info("Model downloaded to %s", model_path)
        return model_path
    except Exception as exc:
        if tmp_path.exists():
            tmp_path.unlink()
        raise RuntimeError(f"Failed to download model from MODEL_URL: {exc}") from exc
