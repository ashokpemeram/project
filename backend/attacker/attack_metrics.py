from __future__ import annotations

from typing import Literal

import torch
import torch.nn.functional as F


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


def _gaussian_kernel(window_size: int, sigma: float, channels: int, device: torch.device, dtype: torch.dtype) -> Tensor:
    coords = torch.arange(window_size, device=device, dtype=dtype) - window_size // 2
    gaussian = torch.exp(-(coords ** 2) / (2 * sigma ** 2))
    gaussian = gaussian / gaussian.sum()
    kernel_2d = gaussian[:, None] * gaussian[None, :]
    kernel = kernel_2d.expand(channels, 1, window_size, window_size).contiguous()
    return kernel


def compute_ssim(
    x: Tensor,
    y: Tensor,
    reduction: Reduction = "mean",
    window_size: int = 11,
    sigma: float = 1.5,
    k1: float = 0.01,
    k2: float = 0.03,
    eps: float = 1e-8,
) -> Tensor:
    _validate_pair(x, y)

    if x.dim() == 3:
        x = x.unsqueeze(0)
        y = y.unsqueeze(0)
    if x.dim() != 4:
        raise ValueError(f"Expected input with 4 dims, got {x.dim()}.")

    x = to_unit_interval(x)
    y = to_unit_interval(y)

    channels = x.size(1)
    kernel = _gaussian_kernel(window_size, sigma, channels, x.device, x.dtype)
    padding = window_size // 2

    mu_x = F.conv2d(x, kernel, groups=channels, padding=padding)
    mu_y = F.conv2d(y, kernel, groups=channels, padding=padding)

    mu_x2 = mu_x.pow(2)
    mu_y2 = mu_y.pow(2)
    mu_xy = mu_x * mu_y

    sigma_x2 = F.conv2d(x * x, kernel, groups=channels, padding=padding) - mu_x2
    sigma_y2 = F.conv2d(y * y, kernel, groups=channels, padding=padding) - mu_y2
    sigma_xy = F.conv2d(x * y, kernel, groups=channels, padding=padding) - mu_xy

    sigma_x2 = sigma_x2.clamp_min(0.0)
    sigma_y2 = sigma_y2.clamp_min(0.0)

    c1 = (k1 ** 2)
    c2 = (k2 ** 2)

    numerator = (2 * mu_xy + c1) * (2 * sigma_xy + c2)
    denominator = (mu_x2 + mu_y2 + c1) * (sigma_x2 + sigma_y2 + c2)

    ssim_map = numerator / (denominator + eps)
    per_sample = ssim_map.mean(dim=(1, 2, 3))

    if reduction == "none":
        return per_sample
    if reduction == "mean":
        return per_sample.mean()
    raise ValueError(f"Unsupported reduction '{reduction}'.")


def summarize_metrics(original: Tensor, protected: Tensor, attacked: Tensor) -> dict[str, Tensor]:
    return {
        "mse_protected_vs_original": compute_mse(protected, original),
        "psnr_protected_vs_original": compute_psnr(protected, original),
        "ssim_protected_vs_original": compute_ssim(protected, original),
        "mse_attacked_vs_original": compute_mse(attacked, original),
        "psnr_attacked_vs_original": compute_psnr(attacked, original),
        "ssim_attacked_vs_original": compute_ssim(attacked, original),
    }


__all__ = [
    "compute_mse",
    "compute_psnr",
    "compute_ssim",
    "summarize_metrics",
    "to_unit_interval",
]
