"""Structured-output schemas, one per node that talks to a model.

Kept separate from state.py on purpose: these are what we FORCE the model to
produce (validated via tool-calling, through .with_structured_output), while
state.py is what the GRAPH stores. Each node translates between the two.
"""
from typing import Literal

from pydantic import BaseModel, Field


class ExtractedFacts(BaseModel):
    facts: list[str] = Field(
        description="3-8 atomic factual claims asserted by this source, each "
        "a self-contained sentence, in your own words."
    )


class ReasonerOutput(BaseModel):
    hypothesis: str = Field(description="One coherent legal hypothesis for how the dispute resolves.")
    support: list[str] = Field(description="Facts (quoted verbatim from the provided list) that back this hypothesis.")


class BranchVerdict(BaseModel):
    branch_id: str
    status: Literal["active", "pruned"]
    score: float = Field(ge=0, le=1)
    reason: str


class CriticOutput(BaseModel):
    verdicts: list[BranchVerdict]
    action: Literal["advance", "continue"]
    reason: str


class SynthesisOutput(BaseModel):
    final_answer: str
