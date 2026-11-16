"""PPO settings for the locally installed RSL-RL 5.x runner."""


def agent_config():
    return {
        "seed": 42,
        "device": "cuda:0",
        "num_steps_per_env": 32,
        "save_interval": 50,
        "check_for_nan": True,
        "logger": "tensorboard",
        "experiment_name": "snu_gom_walk",
        "obs_groups": {"actor": ["policy"], "critic": ["critic"]},
        "actor": {
            "class_name": "MLPModel",
            "hidden_dims": [128, 128, 64],
            "activation": "elu",
            "obs_normalization": True,
            "distribution_cfg": {"class_name": "GaussianDistribution", "init_std": 0.3, "std_type": "log"},
        },
        "critic": {
            "class_name": "MLPModel",
            "hidden_dims": [128, 128, 64],
            "activation": "elu",
            "obs_normalization": True,
        },
        "algorithm": {
            "class_name": "PPO",
            "value_loss_coef": 1.0,
            "use_clipped_value_loss": True,
            "clip_param": 0.2,
            "entropy_coef": 0.005,
            "num_learning_epochs": 4,
            "num_mini_batches": 4,
            "learning_rate": 0.0003,
            "schedule": "adaptive",
            "gamma": 0.99,
            "lam": 0.95,
            "desired_kl": 0.01,
            "max_grad_norm": 1.0,
            "rnd_cfg": None,
            "symmetry_cfg": None,
        },
    }
