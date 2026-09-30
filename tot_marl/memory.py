"""Reducers for GraphState fields where a plain append (operator.add) would be wrong.

`branches` is the one that matters: the Reasoner re-visits the same hypothesis
across depths (extending it), and the Critic re-scores it. Both should update the
existing entry, not pile up duplicates under the same branch_id.
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import Branch


def merge_branches(existing: list["Branch"], updates: list["Branch"]) -> list["Branch"]:
    """Update-by-branch_id reducer. A branch not mentioned in `updates` is left
    untouched; a branch mentioned is shallow-merged (new fields win)."""
    by_id = {b["branch_id"]: dict(b) for b in existing}
    for b in updates:
        by_id[b["branch_id"]] = {**by_id.get(b["branch_id"], {}), **b}
    return list(by_id.values())
