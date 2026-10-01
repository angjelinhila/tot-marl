from tot_marl.graph import build_graph


def test_graph_compiles_with_expected_nodes():
    graph = build_graph()
    nodes = set(graph.get_graph().nodes.keys())
    assert {"dispatch", "scout", "expand", "reasoner", "critic", "synthesis"} <= nodes
