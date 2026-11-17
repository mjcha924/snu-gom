"""Dense supported-lift shaping and conservative touchdown accounting."""

import math

import torch


def reference_tracking_reward(positions, reference, weight=3.0):
    if not math.isfinite(weight) or weight < 0:
        raise ValueError("Reference reward weight must be finite and nonnegative")
    error = (positions - reference) / 0.15
    return weight * torch.exp(-error.square().mean(dim=-1))


def supported_lift_rewards(heights, desired_heights, vertical_forces, weight, moving):
    load = (vertical_forces.clamp_min(0) / weight).clamp(0, 1)
    support = (load.flip(-1) / 0.75).clamp(0, 1)
    active = (desired_heights > 0.002) & moving[:, None]
    progress = (heights.clamp_min(0) / desired_heights.clamp_min(0.002)).clamp(0, 1)
    overshoot = ((heights - desired_heights).clamp_min(0) / 0.005).square()
    lift = (progress * torch.exp(-overshoot) * support * active).sum(dim=-1)
    unloading = ((1 - load) * support * active).sum(dim=-1)
    return lift, unloading


class TouchdownTracker:
    def __init__(self, num_envs, step_dt, device="cpu"):
        if step_dt <= 0:
            raise ValueError("Control timestep must be positive")
        self.minimum_air_frames = math.ceil(0.06 / step_dt - 1e-9)
        self.air_frames = torch.zeros(num_envs, 2, dtype=torch.long, device=device)
        self.cleared = torch.zeros(num_envs, 2, dtype=torch.bool, device=device)
        self.supported = torch.zeros_like(self.cleared)
        self.last_foot = torch.full((num_envs,), -1, dtype=torch.long, device=device)

    def reset(self, env_ids):
        self.air_frames[env_ids] = 0
        self.cleared[env_ids] = False
        self.supported[env_ids] = False
        self.last_foot[env_ids] = -1

    def update(self, contacts, heights, moving, terminal):
        enabled = moving & ~terminal
        self.reset(~enabled)
        opposite = contacts.flip(-1)
        airborne = ~contacts & enabled[:, None]
        beginning = airborne & (self.air_frames == 0)
        self.supported = torch.where(beginning, opposite, self.supported & opposite)
        self.air_frames += airborne.long()
        self.cleared |= airborne & (heights > 0.002)
        touchdown = contacts & self.cleared & self.supported & (self.air_frames >= self.minimum_air_frames) & enabled[:, None]
        foot = touchdown.long().argmax(dim=-1)
        landed = touchdown.any(dim=-1)
        alternating = landed & (self.last_foot >= 0) & (self.last_foot != foot)
        self.last_foot = torch.where(landed, foot, self.last_foot)
        self.air_frames = torch.where(airborne, self.air_frames, 0)
        self.cleared &= airborne
        self.supported &= airborne
        return touchdown, alternating
