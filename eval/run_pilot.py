"""Run one pilot case end-to-end, print the result, and record it as an
episode in eval/history/episodes.jsonl - that history is what lets us answer
"is this actually improving" across runs, not just look at one in isolation.

    python -m eval.run_pilot
    python -m eval.run_pilot data/pilot_cases/example_case.json
"""
import json
import sys
from pathlib import Path

from tot_marl import config as cfg
from tot_marl.graph import build_graph

from .history import record_episode

DEFAULT_CASE = "data/pilot_cases/example_case.json"


def load_case(path: str) -> dict:
    data = json.loads(Path(path).read_text())
    return {
        "case_id": data["case_id"],
        "scout_slices": data["scout_slices"],
        "shared_facts": [],
        "branches": [],
        "depth": 0,
        "final_answer": None,
        "rollout_log": [],
        "llm_call_count": 0,
    }


def _config_snapshot() -> dict:
    return {
        "model": cfg.MODEL_NAME,
        "num_initial_branches": cfg.NUM_INITIAL_BRANCHES,
        "max_tot_depth": cfg.MAX_TOT_DEPTH,
        "use_learned_router": cfg.USE_LEARNED_ROUTER,
    }


def main(case_path: str = DEFAULT_CASE) -> dict:
    graph = build_graph()
    result = graph.invoke(load_case(case_path))
    print(json.dumps(result, indent=2, default=str))

    episode = record_episode(
        case_id=result["case_id"],
        result=result,
        config=_config_snapshot(),
    )

    rs, cm = episode["run_stats"], episode["cooperation_metrics"]
    print(f"\n--- Episode {episode['episode_id']} ({episode['case_id']}, mode={episode['mode']}) ---")
    print(f"  depth_reached:        {rs['depth_reached']}")
    print(f"  branches pruned/final: {rs['num_branches_pruned']}/{rs['num_branches_final']}")
    print(f"  llm_call_count:       {rs['llm_call_count']}")
    print(f"  branch_support_gini:  {cm['branch_support_gini']:.2f}  (0=even draw across sources, 1=one source dominates)")
    print(f"  branch_diversity:     {cm['branch_diversity']:.2f}  (0=branches converged, 1=fully distinct)")
    print(f"  (ground-truth metrics: pending real pilot set - see docs/EVALUATION.md)")
    print(f"\nAppended to eval/history/episodes.jsonl - run `python -m eval.report` to see this against past runs.")
    return result


if __name__ == "__main__":
    main(*sys.argv[1:])
