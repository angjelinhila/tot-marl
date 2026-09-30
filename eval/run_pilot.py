"""Run one pilot case end-to-end and print the resulting state.

This is the cheapest possible signal on whether the wiring holds together -
run it before spending any tokens on real prompts.

    python -m eval.run_pilot
    python -m eval.run_pilot data/pilot_cases/example_case.json
"""
import json
import sys
from pathlib import Path

from tot_marl.graph import build_graph

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
    }


def main(case_path: str = DEFAULT_CASE) -> dict:
    graph = build_graph()
    result = graph.invoke(load_case(case_path))
    print(json.dumps(result, indent=2, default=str))
    return result


if __name__ == "__main__":
    main(*sys.argv[1:])
