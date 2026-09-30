"""End-to-end smoke test: does the graph produce a real answer with real
model calls? This is the genuine "does it work" signal, but it costs tokens
and needs ANTHROPIC_API_KEY - skipped automatically if one isn't set (e.g. in
CI without secrets configured), rather than failing the whole suite.

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
    assert len(result["shared_facts"]) >= 3          # at least one per scout slice
    assert len(result["rollout_log"]) >= 1
    assert all(b["status"] in ("active", "pruned", "selected") for b in result["branches"])
