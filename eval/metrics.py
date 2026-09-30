"""Stubs for the two evaluation axes from the blueprint (Section 3).

Deliberately left as NotImplementedError rather than fake placeholder numbers -
a metric that silently returns 0.0 is worse than one that fails loudly until
someone decides what "correct" means for it. Fill these in against the pilot
case set; they double as reward-signal sources (policy/reward.py) once real.
"""


# --- Evaluation Point 1: task performance ---

def factual_grounding_rate(final_answer: str, shared_facts: list[str]) -> float:
    """% of claims in final_answer traceable to shared_facts."""
    raise NotImplementedError


def citation_accuracy(final_answer: str, ground_truth_citations: list[str]) -> float:
    """Are the cases/statutes cited in final_answer real and on-point."""
    raise NotImplementedError


# --- Evaluation Point 2: cooperation quality ---

def branch_pruning_accuracy(rollout_log: list[dict], correct_branch_id: str) -> float:
    """Did the Critic prune everything except (something that led to) the
    correct branch, without pruning the correct one along the way."""
    raise NotImplementedError


def communication_signal_to_noise(shared_facts: list[str]) -> float:
    """Useful facts vs. near-duplicate restatements already on the blackboard."""
    raise NotImplementedError
