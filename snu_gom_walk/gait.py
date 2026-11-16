"""Smooth alternating sole-height and fore-aft targets for the stepping experiment."""

import math

import torch


def gait_targets(phase, speed, period, clearance):
    offsets = torch.tensor([0.10, 0.60], device=phase.device, dtype=phase.dtype)
    local_phase = torch.remainder(phase[:, None] - offsets, 1.0)
    swing_fraction = 0.35
    progress = (local_phase / swing_fraction).clamp(0, 1)
    moving = speed[:, None] > 0.005
    swing = (local_phase < swing_fraction) & moving
    blend = progress.square() * (3 - 2 * progress)
    half_excursion = speed[:, None] * period * (1 - swing_fraction) / 2
    swing_x = half_excursion * (2 * blend - 1)
    stance_x = half_excursion * (1 - 2 * (local_phase - swing_fraction) / (1 - swing_fraction))
    horizontal = torch.where(swing, swing_x, stance_x) * moving
    heights = clearance * torch.sin(math.pi * progress).square() * swing
    return swing, heights, horizontal
