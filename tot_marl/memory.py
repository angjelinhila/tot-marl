"""Reducers for GraphState fields where a plain append (operator.add) would be wrong."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import Branch


def merge_branches(existing: list["Branch"], updates: list["Branch"]) -> list["Branch"]:
    by_id = {b["branch_id"]: dict(b) for b in existing}
    for b in updates:
        by_id[b["branch_id"]] = {**by_id.get(b["branch_id"], {}), **b}
    return list(by_id.values())
