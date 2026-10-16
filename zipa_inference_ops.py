"""Pure PyTorch inference equivalents of ZIPA's two k2 Swoosh activations.

Formulas from ZIPA/icefall scaling.py (Xiaomi, Apache-2.0). Training is unsupported.
This allows the published checkpoint to run on a Mac without CUDA/k2.
"""
import torch

def swoosh_l_forward(x):
    return torch.nn.functional.softplus(x - 4.0) - 0.08 * x - 0.035

def swoosh_r_forward(x):
    return torch.nn.functional.softplus(x - 1.0) - 0.08 * x - 0.313261687
