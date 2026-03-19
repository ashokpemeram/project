from __future__ import annotations

from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F

from attack_metrics import summarize_metrics, to_unit_interval
from attacker import Attacker, build_default_training_attacker


Tensor = torch.Tensor


def build_training_attacker(device: torch.device | str | None = None) -> Attacker:
    attacker = build_default_training_attacker()
    if device is not None:
        attacker = attacker.to(device)
    attacker.eval()
    return attacker


def compute_attack_distance(attacked: Tensor, original: Tensor) -> Tensor:
    if attacked.shape != original.shape:
        raise ValueError(
            f"Expected attacked and original tensors to match, got {tuple(attacked.shape)} and {tuple(original.shape)}."
        )
    return (attacked - original).abs().mean(dim=(1, 2, 3))


def compute_attack_loss(attacked: Tensor, original: Tensor, margin: float = 0.12) -> Tensor:
    attack_distance = compute_attack_distance(attacked, original)
    return F.relu(margin - attack_distance).mean()


def generator_step_with_attacker(
    generator: nn.Module,
    discriminator: nn.Module,
    attacker: nn.Module,
    original: Tensor,
    noise: Tensor,
    real_labels: Tensor,
    adversarial_criterion: nn.Module,
    identity_criterion: nn.Module,
    lambda_identity: float = 10.0,
    lambda_attack: float = 2.0,
    attack_margin: float = 0.12,
) -> dict[str, Tensor]:
    protected = generator(original, noise)
    attacked = attacker(protected)

    adv_loss = adversarial_criterion(discriminator(protected), real_labels)
    identity_loss = identity_criterion(protected, original)
    attack_distance = compute_attack_distance(attacked, original)
    attack_loss = F.relu(attack_margin - attack_distance).mean()

    g_loss = adv_loss + lambda_identity * identity_loss + lambda_attack * attack_loss

    return {
        "protected": protected,
        "attacked": attacked,
        "adv_loss": adv_loss,
        "identity_loss": identity_loss,
        "attack_loss": attack_loss,
        "attack_distance": attack_distance.mean(),
        "g_loss": g_loss,
    }


@torch.no_grad()
def run_attack_inference(
    generator: nn.Module,
    original: Tensor,
    noise: Tensor,
    attacker: nn.Module | None = None,
) -> dict[str, Tensor]:
    if attacker is None:
        attacker = build_default_training_attacker().to(original.device)
    attacker.eval()
    generator.eval()

    protected = generator(original, noise)
    attacked = attacker(protected)

    return {
        "original": original,
        "protected": protected,
        "attacked": attacked,
        "difference": (attacked - original).abs(),
    }


def collect_validation_metrics(original: Tensor, protected: Tensor, attacked: Tensor) -> dict[str, Tensor]:
    metrics = summarize_metrics(original=original, protected=protected, attacked=attacked)
    metrics["attack_distance"] = compute_attack_distance(attacked, original).mean()
    return metrics


def visualize_attack_pipeline(
    original: Tensor,
    protected: Tensor,
    attacked: Tensor,
    sample_index: int = 0,
    figure_size: tuple[int, int] = (16, 4),
) -> Any:
    import matplotlib.pyplot as plt

    original_01 = to_unit_interval(original)
    protected_01 = to_unit_interval(protected)
    attacked_01 = to_unit_interval(attacked)

    diff = (attacked - original).abs()
    diff = diff / diff.amax(dim=(2, 3), keepdim=True).clamp_min(1e-8)

    panels = [
        ("Original", original_01[sample_index, 0]),
        ("Protected", protected_01[sample_index, 0]),
        ("Attacked", attacked_01[sample_index, 0]),
        ("Difference", diff[sample_index, 0]),
    ]

    fig, axes = plt.subplots(1, 4, figsize=figure_size)
    for axis, (title, image) in zip(axes, panels):
        axis.imshow(image.detach().cpu(), cmap="gray", vmin=0.0, vmax=1.0)
        axis.set_title(title)
        axis.axis("off")

    fig.tight_layout()
    return fig


TRAINING_LOOP_SNIPPET = """
attacker = build_training_attacker(device=device)

# Inside the generator update:
outputs = generator_step_with_attacker(
    generator=generator,
    discriminator=discriminator,
    attacker=attacker,
    original=real_images,
    noise=noise,
    real_labels=real_labels,
    adversarial_criterion=adversarial_criterion,
    identity_criterion=identity_criterion,
    lambda_identity=10.0,
    lambda_attack=2.0,
    attack_margin=0.12,
)

g_loss = outputs["g_loss"]
g_optimizer.zero_grad(set_to_none=True)
g_loss.backward()
g_optimizer.step()
"""


INFERENCE_SNIPPET = """
attacker = Attacker(
    "combined",
    attacks=[
        Attacker("noise", std=0.05).attack,
        Attacker("blur", kernel_size=5).attack,
        Attacker("patch", size_frac=(0.08, 0.18), value_range=(0.25, 0.55), blend=0.85).attack,
        Attacker("cutout", size_frac=(0.08, 0.18), fill_mode="sample_mean").attack,
    ],
    probs=[0.8, 0.6, 0.4, 0.4],
).to(device).eval()

with torch.no_grad():
    protected = generator(original, noise)
    attacked = attacker(protected)

metrics = collect_validation_metrics(original, protected, attacked)
fig = visualize_attack_pipeline(original, protected, attacked)
"""


__all__ = [
    "INFERENCE_SNIPPET",
    "TRAINING_LOOP_SNIPPET",
    "build_training_attacker",
    "collect_validation_metrics",
    "compute_attack_distance",
    "compute_attack_loss",
    "generator_step_with_attacker",
    "run_attack_inference",
    "visualize_attack_pipeline",
]
