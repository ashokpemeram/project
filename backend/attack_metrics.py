from __future__ import annotations

from typing import Literal

import torch


Tensor = torch.Tensor
Reduction = Literal["mean", "none"]


def _validate_pair(x: Tensor, y: Tensor) -> None:
    if not isinstance(x, torch.Tensor) or not isinstance(y, torch.Tensor):
        raise TypeError("Inputs must be torch tensors.")
    if x.shape != y.shape:
        raise ValueError(f"Expected matching shapes, got {tuple(x.shape)} and {tuple(y.shape)}.")
    if x.dtype != y.dtype:
        raise ValueError(f"Expected matching dtypes, got {x.dtype} and {y.dtype}.")


def to_unit_interval(x: Tensor) -> Tensor:
    return ((x + 1.0) / 2.0).clamp(0.0, 1.0)


def compute_mse(x: Tensor, y: Tensor, reduction: Reduction = "mean") -> Tensor:
    _validate_pair(x, y)
    diff = (to_unit_interval(x) - to_unit_interval(y)).pow(2)
    reduce_dims = tuple(range(1, diff.dim()))
    per_sample = diff.mean(dim=reduce_dims)

    if reduction == "none":
        return per_sample
    if reduction == "mean":
        return per_sample.mean()
    raise ValueError(f"Unsupported reduction '{reduction}'.")


def compute_psnr(x: Tensor, y: Tensor, reduction: Reduction = "mean", eps: float = 1e-8) -> Tensor:
    mse = compute_mse(x, y, reduction="none")
    psnr = 10.0 * torch.log10(1.0 / (mse + eps))

    if reduction == "none":
        return psnr
    if reduction == "mean":
        return psnr.mean()
    raise ValueError(f"Unsupported reduction '{reduction}'.")


def summarize_metrics(original: Tensor, protected: Tensor, attacked: Tensor) -> dict[str, Tensor]:
    return {
        "mse_protected_vs_original": compute_mse(protected, original),
        "psnr_protected_vs_original": compute_psnr(protected, original),
        "mse_attacked_vs_original": compute_mse(attacked, original),
        "psnr_attacked_vs_original": compute_psnr(attacked, original),
    }


__all__ = [
    "compute_mse",
    "compute_psnr",
    "summarize_metrics",
    "to_unit_interval",
]
