"""R_total = R_task + R_efficiency + R_consensus (blueprint Section 5.2).

These are pure functions on a finished rollout - nothing here calls a trainer.
"""


def r_task(final_answer: str, ground_truth: str) -> float:
    return 1.0 if final_answer == ground_truth else 0.0


def r_efficiency(total_tokens: int, total_turns: int, alpha: float = 1e-4, beta: float = 1e-2) -> float:
    return -alpha * total_tokens - beta * total_turns


def r_consensus(rollout_log: list[dict], gamma: float = 0.2) -> float:
    correct_prunes = sum(1 for e in rollout_log if e.get("verdict") == "correct_prune")
    return gamma * correct_prunes


def total_reward(final_answer, ground_truth, total_tokens, total_turns, rollout_log) -> float:
    return (
        r_task(final_answer, ground_truth)
        + r_efficiency(total_tokens, total_turns)
        + r_consensus(rollout_log)
    )
