"""Central config. Nothing clever here on purpose - one file, one glance to see
every knob that changes how a run behaves.
"""
import os

MODEL_NAME = os.getenv("TOT_MARL_MODEL", "claude-sonnet-5")

NUM_INITIAL_BRANCHES = 3
MAX_TOT_DEPTH = 3

USE_LEARNED_ROUTER = os.getenv("TOT_MARL_USE_LEARNED_ROUTER", "false").lower() == "true"
LEARNED_ROUTER_CHECKPOINT = os.getenv("PI_PHI_CHECKPOINT", "checkpoints/pi_phi_latest.pt")
