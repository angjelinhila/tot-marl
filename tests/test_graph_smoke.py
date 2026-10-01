"""End-to-end smoke test: real model calls, needs ANTHROPIC_API_KEY - skipped
automatically if one isn't set.

    ANTHROPIC_API_KEY=sk-... pytest tests/test_graph_smoke.py -v -s
"""
import os

import pytest

from eval.run_pilot import DEFAULT_CASE, load_case
from tot_marl.graph import build_graph

pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="needs a real ANTHROPIC_API_KEY - set it in .env to run this for real",
)


def test_graph_runs_end_to_end():
    graph = build_graph()
    result = graph.invoke(load_case(DEFAULT_CASE))

    assert result["final_answer"] is not None
    assert len(result["shared_facts"]) >= 3
    assert len(result["rollout_log"]) >= 1
    assert result["llm_call_count"] > 0
    assert all(b["status"] in ("active", "pruned", "selected") for b in result["branches"])
