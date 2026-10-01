"""Episode history: every pilot run gets appended here as one JSON line, so
we can see whether metrics are actually moving across prompt/code changes
over time - not just look at one run in isolation.

Deliberately version-controlled (NOT in .gitignore). The point is a
persistent, diffable record across commits: "did the Synthesis prompt change
in commit X actually help?" is a question about this file's git history, not
just about today's run.
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import metrics as M

HISTORY_PATH = Path(__file__).parent / "history" / "episodes.jsonl"


def _branch_summary(branches: list[dict]) -> list[dict]:
    return [
        {
            "branch_id": b["branch_id"],
            "status": b["status"],
            "score": b["score"],
            "hypothesis": b["hypothesis"],
            "support": b["support"],
        }
        for b in branches
    ]


def record_episode(
    case_id: str,
    result: dict,
    config: dict,
    mode: str = "baseline",
    ground_truth: Optional[dict] = None,
) -> dict:
    """Append one episode to history/episodes.jsonl and return it.

    `result` is the raw dict returned by graph.invoke(...).
    `config` is a snapshot of the knobs that produced this run (model name,
    NUM_INITIAL_BRANCHES, MAX_TOT_DEPTH, USE_LEARNED_ROUTER, ...) - without
    this, a metric change across episodes is ambiguous: did the prompt
    change, or did someone just bump MAX_TOT_DEPTH?
    `mode` distinguishes baseline runs from future decomposition ablations
    (e.g. "oracle_critic", "auto_advance" - see docs/EVALUATION.md) so they
    can share this same history file and be filtered apart later.
    `ground_truth` is optional - pass it once a pilot case has a real,
    labeled outcome. Tier 1 metrics (eval/metrics.py) plug into
    "ground_truth_metrics" once implemented; until then this just stores the
    label for later re-scoring, rather than computing anything.
    """
    branches = result["branches"]
    episode = {
        "episode_id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "case_id": case_id,
        "mode": mode,
        "config": config,
        "run_stats": {
            "depth_reached": result["depth"],
            "num_branches_final": len(branches),
            "num_branches_pruned": len([b for b in branches if b["status"] == "pruned"]),
            "llm_call_count": result.get("llm_call_count"),
        },
        "cooperation_metrics": {
            "branch_support_gini": M.branch_support_gini(branches, result["shared_facts"]),
            "branch_diversity": M.branch_diversity(branches),
        },
        "ground_truth": ground_truth,
        "ground_truth_metrics": None,  # Tier 1 metrics land here once eval/metrics.py's
                                        # ground-truth functions are implemented
        "final_answer": result["final_answer"],
        "branches": _branch_summary(branches),
        "rollout_log": result["rollout_log"],
    }

    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "a") as f:
        f.write(json.dumps(episode) + "\n")

    return episode


def load_history() -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    with open(HISTORY_PATH) as f:
        return [json.loads(line) for line in f if line.strip()]
