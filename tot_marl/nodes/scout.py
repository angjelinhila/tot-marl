"""Scout layer. Each scout owns one asymmetric slice of the corpus (blueprint
Section 2: "no single scout can solve the task alone"). The number of scouts
isn't fixed at graph-compile time, so the fan-out uses Send rather than a
static edge - this is LangGraph's map-reduce pattern, applied to scouts
instead of documents.
"""
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Send

from ..llm import get_llm
from ..schemas import ExtractedFacts
from ..state import GraphState

_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a Scout agent in a legal-reasoning pipeline. You only see one "
     "source's framing of a dispute - here, the '{role}' side. Extract the "
     "concrete, atomic factual claims asserted in the text below. Report what "
     "is CLAIMED, not whether it's true or who's right - a later agent will "
     "weigh conflicting claims from other scouts against each other. Write "
     "each fact as a self-contained sentence, in your own words."),
    ("human", "{raw_text}"),
])


def dispatch_scouts(state: GraphState) -> list[Send]:
    return [
        Send("scout", {"scout_slice": s, "case_id": state["case_id"]})
        for s in state["scout_slices"]
    ]


def scout_node(payload: dict) -> dict:
    slice_ = payload["scout_slice"]
    chain = _PROMPT | get_llm().with_structured_output(ExtractedFacts)
    result: ExtractedFacts = chain.invoke({"role": slice_["role"], "raw_text": slice_["raw_text"]})
    tagged = [f"[{slice_['role']}] {fact}" for fact in result.facts]
    return {"shared_facts": tagged, "llm_call_count": 1}
