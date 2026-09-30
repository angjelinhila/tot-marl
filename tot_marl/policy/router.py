"""The swap point described in blueprint Section 5.4: pi_phi sits on top of
the pipeline, deciding orchestration moves - never the content of an agent's
reasoning. LLMRouter and LearnedRouter both implement RoutingPolicy, so
critic.py never needs to know which one it's talking to.
"""
from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate

from .. import config
from ..llm import get_llm
from ..schemas import CriticOutput
from ..state import Branch, GraphState

_CRITIC_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are the Critic in a Tree-of-Thought legal analysis. Below are "
     "several competing hypotheses (branches) and the full pool of shared "
     "facts, including facts a given branch did not cite. For EACH branch: "
     "check whether its cited support actually backs its hypothesis, and "
     "whether it holds up against facts it ignored. Mark weak or contradicted "
     "branches 'pruned'; keep genuinely defensible ones 'active'. Then decide "
     "overall: 'advance' if only one strong branch remains (or the survivors "
     "differ only in minor detail), or 'continue' if multiple genuinely "
     "different theories are still alive and worth developing further."),
    ("human", "Branches:\n{branches}\n\nAll shared facts:\n{facts}"),
])


def _format_branches(branches: list[Branch]) -> str:
    """Pure and network-free on purpose - the one piece of this file cheap to
    unit-test without a model call."""
    return "\n\n".join(
        f"[{b['branch_id']}] {b['hypothesis']}\nCited support: {b['support']}"
        for b in branches
        if b["status"] != "pruned"
    )


@dataclass
class RoutingDecision:
    action: str  # "advance" | "continue"
    updated_branches: list[Branch]
    reason: str = ""


class RoutingPolicy:
    def decide(self, state: GraphState) -> RoutingDecision:
        raise NotImplementedError


class LLMRouter(RoutingPolicy):
    """Today's implementation: an LLM scores and prunes branches on request."""

    def decide(self, state: GraphState) -> RoutingDecision:
        chain = _CRITIC_PROMPT | get_llm().with_structured_output(CriticOutput)
        result: CriticOutput = chain.invoke({
            "branches": _format_branches(state["branches"]),
            "facts": "\n".join(state["shared_facts"]),
        })
        verdict_by_id = {v.branch_id: v for v in result.verdicts}
        updated = [
            {**b, "status": verdict_by_id[b["branch_id"]].status, "score": verdict_by_id[b["branch_id"]].score}
            if b["branch_id"] in verdict_by_id else b
            for b in state["branches"]
        ]
        return RoutingDecision(action=result.action, updated_branches=updated, reason=result.reason)


class LearnedRouter(RoutingPolicy):
    """Placeholder for a trained pi_phi (blueprint Section 5.1: MAPPO or GRPO
    over exactly this decision). Same RoutingDecision contract as LLMRouter -
    that's what lets config.USE_LEARNED_ROUTER flip the whole system over
    without touching critic.py or graph.py.
    """

    def __init__(self, checkpoint_path: str):
        self.checkpoint_path = checkpoint_path
        raise NotImplementedError(
            "No trained checkpoint yet - train pi_phi first (see policy/reward.py "
            "and the blueprint's Section 5) before flipping config.USE_LEARNED_ROUTER."
        )

    def decide(self, state: GraphState) -> RoutingDecision:
        raise NotImplementedError


def get_router() -> RoutingPolicy:
    if config.USE_LEARNED_ROUTER:
        return LearnedRouter(checkpoint_path=config.LEARNED_ROUTER_CHECKPOINT)
    return LLMRouter()
