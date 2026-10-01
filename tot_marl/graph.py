"""Wires the pipeline from the blueprint's Section 2 diagram:

    scout (Send fan-out, dynamic count)
      -> expand -> reasoner (Send fan-out) -> critic  [looped until advance/depth cap]
      -> synthesis

Deliberately flat rather than nesting expand/reasoner/critic as a subgraph:
a compiled subgraph that shares its parent's exact state schema echoes back
every field on its way out - including ones it never touched - and an
additive reducer (like shared_facts' operator.add) then double-counts it.
Flattening sidesteps that gotcha.
"""
from langgraph.graph import END, START, StateGraph

from .nodes.critic import critic_router
from .nodes.reasoner import expand_branches, reasoner_node
from .nodes.scout import dispatch_scouts, scout_node
from .nodes.synthesis import synthesis_node
from .state import GraphState


def _noop(_state: GraphState) -> dict:
    return {}


def build_graph():
    g = StateGraph(GraphState)
    g.add_node("dispatch", _noop)
    g.add_node("scout", scout_node)
    g.add_node("expand", _noop)
    g.add_node("reasoner", reasoner_node)
    g.add_node("critic", critic_router)
    g.add_node("synthesis", synthesis_node)

    g.add_edge(START, "dispatch")
    g.add_conditional_edges("dispatch", dispatch_scouts, ["scout"])
    g.add_edge("scout", "expand")
    g.add_conditional_edges("expand", expand_branches, ["reasoner"])
    g.add_edge("reasoner", "critic")
    g.add_edge("synthesis", END)
    return g.compile()
