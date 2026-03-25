from __future__ import annotations

import torch

from .attack_metrics import compute_mse, compute_psnr
from .attacker import Attacker, BlurAttack, CutoutAttack, GaussianNoiseAttack, PatchAttack
from .attacker_integration import build_training_attacker, compute_attack_loss


def _assert_in_range(x: torch.Tensor) -> None:
    if x.min().item() < -1.00001 or x.max().item() > 1.00001:
        raise AssertionError("Tensor left the expected [-1, 1] range.")


def _run_shape_and_range_checks(device: torch.device) -> None:
    x = torch.linspace(-1.0, 1.0, steps=2 * 1 * 64 * 64, device=device).reshape(2, 1, 64, 64)

    attacks = [
        GaussianNoiseAttack(std=0.05).to(device),
        BlurAttack(kernel_size=5).to(device),
        PatchAttack().to(device),
        CutoutAttack().to(device),
        build_training_attacker(device=device),
        Attacker("combined", attacks=[GaussianNoiseAttack(0.02), BlurAttack(3)], probs=[1.0, 1.0]).to(device),
    ]

    for attack in attacks:
        out = attack(x)
        if out.shape != x.shape:
            raise AssertionError(f"{attack.__class__.__name__} changed tensor shape.")
        if out.device != x.device:
            raise AssertionError(f"{attack.__class__.__name__} changed device placement.")
        if out.dtype != x.dtype:
            raise AssertionError(f"{attack.__class__.__name__} changed dtype.")
        _assert_in_range(out)


def _run_gradient_check(device: torch.device) -> None:
    protected = torch.randn(2, 1, 64, 64, device=device).clamp(-1.0, 1.0).requires_grad_(True)
    attacker = build_training_attacker(device=device)
    loss = attacker(protected).mean()
    loss.backward()

    if protected.grad is None:
        raise AssertionError("Gradient check failed: no gradient was produced.")
    if not torch.isfinite(protected.grad).all():
        raise AssertionError("Gradient check failed: non-finite gradients were produced.")


def _run_metric_sanity_check(device: torch.device) -> None:
    original = torch.zeros(2, 1, 64, 64, device=device)
    protected = original.clone()
    attacked = PatchAttack(size_frac=(0.25, 0.25), value_range=(0.8, 0.8), blend=1.0).to(device)(protected)

    protected_mse = compute_mse(protected, original)
    attacked_mse = compute_mse(attacked, original)
    protected_psnr = compute_psnr(protected, original)
    attacked_psnr = compute_psnr(attacked, original)
    attack_loss = compute_attack_loss(attacked, original, margin=0.12)

    if protected_mse.item() > 1e-8:
        raise AssertionError("Protected-vs-original MSE sanity check failed.")
    if attacked_mse.item() <= protected_mse.item():
        raise AssertionError("Attacked-vs-original MSE did not increase.")
    if attacked_psnr.item() >= protected_psnr.item():
        raise AssertionError("Attacked-vs-original PSNR did not decrease.")
    if attack_loss.item() < 0.0:
        raise AssertionError("Attack loss must stay non-negative.")


def main() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _run_shape_and_range_checks(device)
    _run_gradient_check(device)
    _run_metric_sanity_check(device)
    print(f"Attacker smoke tests passed on {device}.")


if __name__ == "__main__":
    main()
