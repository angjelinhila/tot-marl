"""Graph wiring check - no model calls, no API key needed. Compiling the
graph and inspecting its node/edge structure is enough to catch import errors
or a broken wire without spending a single token.
"""
from tot_marl.graph import build_graph


def test_graph_compiles_with_expected_nodes():
    graph = build_graph()
    nodes = set(graph.get_graph().nodes.keys())
    assert {"dispatch", "scout", "expand", "reasoner", "critic", "synthesis"} <= nodes
