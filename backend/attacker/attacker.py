from __future__ import annotations

from typing import Iterable, Sequence

import torch
import torch.nn as nn
import torch.nn.functional as F


Tensor = torch.Tensor


def _validate_fraction_range(name: str, value: tuple[float, float]) -> tuple[float, float]:
    if len(value) != 2:
        raise ValueError(f"{name} must contain exactly two values.")
    low, high = value
    if not (0.0 < low <= high <= 1.0):
        raise ValueError(f"{name} must satisfy 0.0 < low <= high <= 1.0.")
    return float(low), float(high)


def _validate_value_range(name: str, value: tuple[float, float]) -> tuple[float, float]:
    if len(value) != 2:
        raise ValueError(f"{name} must contain exactly two values.")
    low, high = value
    if not (-1.0 <= low <= high <= 1.0):
        raise ValueError(f"{name} must stay inside [-1, 1].")
    return float(low), float(high)


class BaseAttack(nn.Module):
    """Base class for image attacks operating on grayscale tensors in [-1, 1]."""

    def __init__(self) -> None:
        super().__init__()

    def validate_input(self, x: Tensor) -> None:
        if not isinstance(x, torch.Tensor):
            raise TypeError("Attack input must be a torch.Tensor.")
        if x.dim() != 4:
            raise ValueError(f"Expected input with 4 dimensions, got shape {tuple(x.shape)}.")
        if x.size(1) != 1:
            raise ValueError(f"Expected a single grayscale channel, got {x.size(1)} channels.")
        if not x.is_floating_point():
            raise TypeError("Attack input must use a floating point dtype.")

    def clamp(self, x: Tensor) -> Tensor:
        return x.clamp(-1.0, 1.0)

    def forward(self, x: Tensor) -> Tensor:
        self.validate_input(x)
        attacked = self._forward_impl(x)
        if attacked.shape != x.shape:
            raise RuntimeError(
                f"{self.__class__.__name__} changed shape from {tuple(x.shape)} to {tuple(attacked.shape)}."
            )
        return self.clamp(attacked)

    def _forward_impl(self, x: Tensor) -> Tensor:
        raise NotImplementedError


class GaussianNoiseAttack(BaseAttack):
    def __init__(self, std: float = 0.05) -> None:
        super().__init__()
        if std < 0.0:
            raise ValueError("std must be non-negative.")
        self.std = float(std)

    def _forward_impl(self, x: Tensor) -> Tensor:
        if self.std == 0.0:
            return x
        return x + torch.randn_like(x) * self.std


class BlurAttack(BaseAttack):
    def __init__(self, kernel_size: int = 5) -> None:
        super().__init__()
        if kernel_size < 1 or kernel_size % 2 == 0:
            raise ValueError("kernel_size must be a positive odd integer.")
        self.kernel_size = int(kernel_size)

    def _forward_impl(self, x: Tensor) -> Tensor:
        padding = self.kernel_size // 2
        return F.avg_pool2d(x, kernel_size=self.kernel_size, stride=1, padding=padding)


class RegionAttack(BaseAttack):
    def __init__(self, size_frac: tuple[float, float]) -> None:
        super().__init__()
        self.size_frac = _validate_fraction_range("size_frac", size_frac)

    def _region_mask(self, x: Tensor) -> Tensor:
        batch_size, _, height, width = x.shape
        spatial_limit = min(height, width)
        min_frac, max_frac = self.size_frac

        min_size = max(1, int(round(spatial_limit * min_frac)))
        max_size = max(min_size, int(round(spatial_limit * max_frac)))

        mask = x.new_zeros((batch_size, 1, height, width))

        for idx in range(batch_size):
            if min_size == max_size:
                side = min_size
            else:
                side = int(torch.randint(min_size, max_size + 1, (1,), device=x.device).item())

            max_top = max(height - side, 0)
            max_left = max(width - side, 0)
            top = int(torch.randint(0, max_top + 1, (1,), device=x.device).item())
            left = int(torch.randint(0, max_left + 1, (1,), device=x.device).item())
            mask[idx, :, top : top + side, left : left + side] = 1.0

        return mask


class PatchAttack(RegionAttack):
    def __init__(
        self,
        size_frac: tuple[float, float] = (0.08, 0.18),
        value_range: tuple[float, float] = (0.25, 0.55),
        blend: float = 0.85,
    ) -> None:
        super().__init__(size_frac=size_frac)
        self.value_range = _validate_value_range("value_range", value_range)
        if not (0.0 <= blend <= 1.0):
            raise ValueError("blend must stay inside [0, 1].")
        self.blend = float(blend)

    def _forward_impl(self, x: Tensor) -> Tensor:
        mask = self._region_mask(x)
        low, high = self.value_range
        patch_values = x.new_empty((x.size(0), 1, 1, 1)).uniform_(low, high)
        alpha = mask * self.blend
        return x * (1.0 - alpha) + patch_values * alpha


class CutoutAttack(RegionAttack):
    def __init__(
        self,
        size_frac: tuple[float, float] = (0.08, 0.18),
        fill_mode: str = "sample_mean",
        fill_value: float = 0.0,
    ) -> None:
        super().__init__(size_frac=size_frac)
        self.fill_mode = fill_mode.lower()
        if self.fill_mode not in {"sample_mean", "constant"}:
            raise ValueError("fill_mode must be either 'sample_mean' or 'constant'.")
        if not (-1.0 <= fill_value <= 1.0):
            raise ValueError("fill_value must stay inside [-1, 1].")
        self.fill_value = float(fill_value)

    def _get_fill(self, x: Tensor) -> Tensor:
        if self.fill_mode == "sample_mean":
            return x.mean(dim=(2, 3), keepdim=True)
        return x.new_full((x.size(0), 1, 1, 1), self.fill_value)

    def _forward_impl(self, x: Tensor) -> Tensor:
        mask = self._region_mask(x)
        fill = self._get_fill(x)
        return x * (1.0 - mask) + fill * mask


class CombinedAttack(BaseAttack):
    def __init__(self, attacks: Sequence[nn.Module], probs: Sequence[float] | None = None) -> None:
        super().__init__()
        if not attacks:
            raise ValueError("CombinedAttack requires at least one child attack.")
        self.attacks = nn.ModuleList(attacks)

        if probs is None:
            probs = [1.0] * len(attacks)
        if len(probs) != len(attacks):
            raise ValueError("probs must match the number of child attacks.")

        validated_probs: list[float] = []
        for prob in probs:
            if not (0.0 <= float(prob) <= 1.0):
                raise ValueError("Each probability must stay inside [0, 1].")
            validated_probs.append(float(prob))
        self.probs = tuple(validated_probs)

    def _apply_probabilistically(self, current: Tensor, attacked: Tensor, prob: float) -> Tensor:
        if prob <= 0.0:
            return current
        if prob >= 1.0:
            return attacked

        batch_mask = (torch.rand((current.size(0), 1, 1, 1), device=current.device) < prob).to(current.dtype)
        return attacked * batch_mask + current * (1.0 - batch_mask)

    def _forward_impl(self, x: Tensor) -> Tensor:
        current = x
        for attack, prob in zip(self.attacks, self.probs):
            attacked = attack(current)
            current = self._apply_probabilistically(current, attacked, prob)
        return current


class Attacker(nn.Module):
    """Wrapper that builds one attack from a string name."""

    def __init__(self, attack_type: str, **kwargs) -> None:
        super().__init__()
        if not attack_type:
            raise ValueError("attack_type must be provided.")
        self.attack_type = attack_type.lower()
        self.attack = self._build_attack(self.attack_type, **kwargs)

    def _build_attack(self, attack_type: str, **kwargs) -> nn.Module:
        attack_map = {
            "noise": GaussianNoiseAttack,
            "blur": BlurAttack,
            "patch": PatchAttack,
            "cutout": CutoutAttack,
        }

        if attack_type == "combined":
            attacks = kwargs.pop("attacks", None)
            probs = kwargs.pop("probs", None)
            if kwargs:
                unexpected = ", ".join(sorted(kwargs))
                raise TypeError(f"Unexpected keyword arguments for combined attack: {unexpected}")
            if attacks is None:
                raise ValueError("Combined attack requires an 'attacks' sequence.")
            return CombinedAttack(attacks=attacks, probs=probs)

        if attack_type not in attack_map:
            valid = ", ".join(sorted((*attack_map.keys(), "combined")))
            raise ValueError(f"Unknown attack_type '{attack_type}'. Expected one of: {valid}")

        return attack_map[attack_type](**kwargs)

    def forward(self, x: Tensor) -> Tensor:
        return self.attack(x)


def build_default_training_attacker() -> Attacker:
    attacks: Iterable[nn.Module] = (
        GaussianNoiseAttack(std=0.05),
        BlurAttack(kernel_size=5),
        PatchAttack(size_frac=(0.08, 0.18), value_range=(0.25, 0.55), blend=0.85),
        CutoutAttack(size_frac=(0.08, 0.18), fill_mode="sample_mean"),
    )
    return Attacker("combined", attacks=list(attacks), probs=[0.8, 0.6, 0.4, 0.4])


__all__ = [
    "Attacker",
    "BaseAttack",
    "BlurAttack",
    "CombinedAttack",
    "CutoutAttack",
    "GaussianNoiseAttack",
    "PatchAttack",
    "build_default_training_attacker",
]
