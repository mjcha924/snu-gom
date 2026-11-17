"""Smooth joint-space candidates for free-base feasibility tests, not policies."""

import math

import torch


PARAMETERS = ("stance", "lean", "lift", "pitch_bias", "period")


def swing_weights(time, period):
    phase = ((time - 3).clamp_min(0) / period) % 1
    centers = torch.tensor([0.25, 0.75], device=phase.device, dtype=phase.dtype)
    progress = ((phase[..., None] - (centers - 0.10)) / 0.20).clamp(0, 1)
    return torch.sin(math.pi * progress).square()


def ankle_pitch_correction(pitch, angular_velocity, gains):
    if not torch.isfinite(gains).all() or (gains < 0).any():
        raise ValueError("Pitch feedback gains must be finite and nonnegative")
    return (gains[..., 0] * pitch + gains[..., 1] * angular_velocity).clamp(-0.15, 0.15)


def guard_inward_roll(targets, limit):
    guarded = targets.clone()
    guarded[..., 1] = torch.maximum(guarded[..., 1], -limit)
    guarded[..., 6] = torch.minimum(guarded[..., 6], limit)
    return guarded


def probe_targets(time, parameters, initial_stance=0.30):
    stance, lean, lift, pitch_bias, period = parameters.unbind(dim=-1)
    if not torch.isfinite(parameters).all() or (period <= 0).any():
        raise ValueError("Finite parameters and positive periods are required")
    settling = torch.as_tensor(time / 2, device=parameters.device).clamp(0, 1)
    settling = settling.square() * (3 - 2 * settling)
    knee_base = initial_stance + settling * (stance - initial_stance)
    phase = ((time - 3).clamp_min(0) / period) % 1
    roll = lean * torch.tanh(1.5 * torch.sin(2 * math.pi * phase)) / math.tanh(1.5)
    weights = swing_weights(time, period)
    targets = torch.zeros((*parameters.shape[:-1], 10), device=parameters.device, dtype=parameters.dtype)
    for foot in range(2):
        knee = knee_base + lift * weights[..., foot]
        pitch = knee / 2 + pitch_bias * settling
        targets[..., foot * 5 + 1] = -roll
        targets[..., foot * 5 + 2] = pitch
        targets[..., foot * 5 + 3] = knee * (1 if foot == 0 else -1)
        targets[..., foot * 5 + 4] = pitch - knee
    return targets
