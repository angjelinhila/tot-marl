"""Reasoner layer: turns shared facts into competing Tree-of-Thought branches.

First pass (depth 0): fan out NUM_INITIAL_BRANCHES fresh hypotheses.
Later passes: fan out one Send per still-active branch, so a branch is
EXTENDED (same branch_id) rather than silently re-created - the merge_branches
reducer in memory.py depends on that id staying stable.
"""
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Send

from .. import config
from ..llm import get_llm
from ..schemas import ReasonerOutput
from ..state import Branch, GraphState

_NEW_BRANCH_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a Reasoner agent performing Tree-of-Thought legal analysis. "
     "Below are facts gathered from multiple, sometimes conflicting, sources. "
     "Propose ONE coherent hypothesis for how this dispute should resolve. "
     "Other Reasoners are independently proposing their own hypotheses right "
     "now - take a genuinely distinct angle rather than the single most "
     "obvious reading, if the facts can support one. Quote the specific facts "
     "(verbatim, from the list below) that support your hypothesis."),
    ("human", "Shared facts:\n{facts}"),
])

_EXTEND_BRANCH_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are continuing to develop ONE hypothesis in a Tree-of-Thought legal "
     "analysis, for another round of scrutiny. Keep the same underlying "
     "theory - do not switch to an unrelated one - but strengthen it, address "
     "a likely counterargument, or narrow it in light of the full fact pool "
     "below (which may include facts you have not considered yet). Quote the "
     "specific facts (verbatim) that now support it."),
    ("human", "Current hypothesis: {hypothesis}\nCurrent support: {support}\n\n"
              "Full shared facts:\n{facts}"),
])


def expand_branches(state: GraphState) -> list[Send]:
    """Router (attached via add_conditional_edges)."""
    if state["depth"] == 0:
        return [
            Send("reasoner", {"branch_seed": i, "shared_facts": state["shared_facts"], "parent_branch": None})
            for i in range(config.NUM_INITIAL_BRANCHES)
        ]
    active = [b for b in state["branches"] if b["status"] == "active"]
    return [
        Send("reasoner", {"branch_seed": None, "shared_facts": state["shared_facts"], "parent_branch": b})
        for b in active
    ]


def reasoner_node(payload: dict) -> dict:
    facts = payload["shared_facts"]
    parent = payload.get("parent_branch")

    if parent is not None:
        chain = _EXTEND_BRANCH_PROMPT | get_llm().with_structured_output(ReasonerOutput)
        result: ReasonerOutput = chain.invoke({
            "hypothesis": parent["hypothesis"],
            "support": parent["support"],
            "facts": "\n".join(facts),
        })
        branch: Branch = {
            **parent,
            "hypothesis": result.hypothesis,
            "support": result.support,
            "status": "active",
            "score": None,
        }
    else:
        chain = _NEW_BRANCH_PROMPT | get_llm().with_structured_output(ReasonerOutput)
        result = chain.invoke({"facts": "\n".join(facts)})
        branch = {
            "branch_id": f"b{payload['branch_seed']}",
            "hypothesis": result.hypothesis,
            "support": result.support,
            "status": "active",
            "score": None,
        }
    return {"branches": [branch]}
