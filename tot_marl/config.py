"""Central config. Nothing clever here on purpose - one file, one glance to see
every knob that changes how a run behaves.
"""
import os

# Model used by every node. claude-sonnet-5 is the balanced default; swap to
# claude-sonnet-5-5 or claude-opus-5-5 (better, slower, pricier) once you're
# past prompt iteration and want the real ceiling.
MODEL_NAME = os.getenv("TOT_MARL_MODEL", "claude-sonnet-5")

# --- Tree-of-Thought shape ---
NUM_INITIAL_BRANCHES = 3   # hypotheses the Reasoner fans out on the first pass
MAX_TOT_DEPTH = 3          # hard cap on prune/backtrack cycles, so a bad Critic can't loop forever

# --- MARL swap point (blueprint Section 5) ---
# False today: nodes/critic.py uses policy.router.LLMRouter (a prompted LLM call).
# Flip once pi_phi is trained: policy.router.get_router() returns LearnedRouter instead,
# and nothing in graph.py or nodes/critic.py needs to change.
USE_LEARNED_ROUTER = os.getenv("TOT_MARL_USE_LEARNED_ROUTER", "false").lower() == "true"
LEARNED_ROUTER_CHECKPOINT = os.getenv("PI_PHI_CHECKPOINT", "checkpoints/pi_phi_latest.pt")
