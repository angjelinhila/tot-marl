"""Critic: scores every branch, then decides whether to advance to Synthesis or
loop back for another Reasoner pass.

This is the ONE function the whole MARL layer (blueprint Section 5) cares about.
Today `get_router()` returns an LLMRouter (a prompted call). Once training
produces a checkpoint, config.USE_LEARNED_ROUTER flips it to LearnedRouter -
same RoutingDecision contract, so nothing here or in graph.py changes.
"""
from langgraph.types import Command

from .. import config
from ..policy.router import get_router
from ..state import GraphState


def critic_router(state: GraphState) -> Command:
    router = get_router()
    decision = router.decide(state)

    log_entry = {"depth": state["depth"], "action": decision.action, "reason": decision.reason}

    if decision.action == "advance" or state["depth"] >= config.MAX_TOT_DEPTH:
        return Command(
            goto="synthesis",
            update={
                "branches": decision.updated_branches,
                "rollout_log": [log_entry],
                "llm_call_count": decision.llm_calls,
            },
        )
    return Command(
        goto="expand",
        update={
            "branches": decision.updated_branches,
            "depth": state["depth"] + 1,
            "rollout_log": [log_entry],
            "llm_call_count": decision.llm_calls,
        },
    )
