"""The shared graph state. This IS the blackboard from the blueprint's Section 2
diagram - every node reads from it and writes back a partial update; LangGraph
merges updates using the reducer attached to each field (see memory.py for the
non-trivial ones).

Keep this file boring. If a node needs a new piece of shared state, it goes here
first, with a reducer, before it goes anywhere else.
"""
import operator
from typing import Annotated, Optional, TypedDict

from .memory import merge_branches


class ScoutSlice(TypedDict):
    """One scout's asymmetric slice of the raw corpus - set once at run start,
    never merged with anyone else's (that's the whole point)."""
    scout_id: str
    role: str  # e.g. "plaintiff_facts" | "defendant_facts" | "prior_case_law"
    raw_text: str


class Branch(TypedDict):
    """One Tree-of-Thought hypothesis. `branch_id` is the identity the merge
    reducer keys on - reuse it across depths to extend a branch instead of
    silently forking a duplicate."""
    branch_id: str
    hypothesis: str
    support: list[str]           # facts/citations backing this branch
    status: str                  # "active" | "pruned" | "selected"
    score: Optional[float]


class GraphState(TypedDict):
    case_id: str
    scout_slices: list[ScoutSlice]                         # set once, read-only after that
    shared_facts: Annotated[list[str], operator.add]       # append-only blackboard
    branches: Annotated[list[Branch], merge_branches]       # update-by-id, see memory.py
    depth: int
    final_answer: Optional[str]
    rollout_log: Annotated[list[dict], operator.add]       # every routing decision - reward signal later
    llm_call_count: Annotated[int, operator.add]           # one real model call = +1, from any node
