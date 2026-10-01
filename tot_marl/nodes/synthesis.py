"""Synthesis: writes the final answer from branches + facts only.

Notice this function never touches state["scout_slices"] - the "no raw
documents, only reports" constraint from the blueprint is enforced by what
this function simply never sees, not by a prompt instruction the model could
ignore.
"""
from langchain_core.prompts import ChatPromptTemplate

from ..llm import get_llm
from ..schemas import SynthesisOutput
from ..state import GraphState

_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are the Synthesis agent. You have NOT seen the raw case documents - "
     "only the surviving hypothesis/hypotheses below and the shared fact "
     "pool. Write a short, decisive memo: state the conclusion, then justify "
     "it by quoting specific facts from the list. If more than one "
     "hypothesis survived, briefly explain why you favor one. One paragraph."),
    ("human", "Surviving hypotheses:\n{branches}\n\nShared facts:\n{facts}"),
])


def synthesis_node(state: GraphState) -> dict:
    surviving = [b for b in state["branches"] if b["status"] != "pruned"]
    if not surviving:
        return {"final_answer": "No hypothesis survived Critic review - insufficient support in the record.", "llm_call_count": 0}

    branches_text = "\n\n".join(
        f"[{b['branch_id']}, score={b['score']}] {b['hypothesis']}" for b in surviving
    )
    chain = _PROMPT | get_llm().with_structured_output(SynthesisOutput)
    result: SynthesisOutput = chain.invoke({"branches": branches_text, "facts": "\n".join(state["shared_facts"])})
    return {"final_answer": result.final_answer, "llm_call_count": 1}
