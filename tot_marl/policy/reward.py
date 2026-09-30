"""R_total = R_task + R_efficiency + R_consensus (blueprint Section 5.2).

These are pure functions on a finished rollout - nothing here calls a trainer.
They exist now so the eval harness (eval/metrics.py) can be built against the
same signals from day one, per the blueprint's design note: most of the reward
signal should come from the evaluation harness we already need to build, not
from separate plumbing.
"""


def r_task(final_answer: str, ground_truth: str) -> float:
    """TODO: real scoring - citation match, predicted outcome match, rubric
    score. Stub: exact-string placeholder so the pipeline has *something* to
    optimize toward while the real metric gets built.
    """
    return 1.0 if final_answer == ground_truth else 0.0


def r_efficiency(total_tokens: int, total_turns: int, alpha: float = 1e-4, beta: float = 1e-2) -> float:
    """Penalizes yapping / re-stating facts already in shared memory."""
    return -alpha * total_tokens - beta * total_turns


def r_consensus(rollout_log: list[dict], gamma: float = 0.2) -> float:
    """Rewards branches the Critic correctly pruned early. Depends on
    rollout_log entries eventually carrying a ground-truth-checked verdict,
    not just the action taken - that verdict comes from eval/metrics.py.
    """
    correct_prunes = sum(1 for e in rollout_log if e.get("verdict") == "correct_prune")
    return gamma * correct_prunes


def total_reward(
    final_answer: str,
    ground_truth: str,
    total_tokens: int,
    total_turns: int,
    rollout_log: list[dict],
) -> float:
    return (
        r_task(final_answer, ground_truth)
        + r_efficiency(total_tokens, total_turns)
        + r_consensus(rollout_log)
    )
