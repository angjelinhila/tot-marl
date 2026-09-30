"""Single place every node gets its model client from. Swap models, add
retry/rate-limit handling, or point at a different provider here - nothing
else in the codebase should construct a ChatAnthropic directly.
"""
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

from . import config

load_dotenv()  # picks up ANTHROPIC_API_KEY from a local .env, if present


def get_llm() -> ChatAnthropic:
    # temperature=0: every node here is making a structured judgment call
    # (extract/hypothesize/score/write), not brainstorming - repeatability
    # matters more than variety. Raise it for the Reasoner specifically later
    # if branches end up too similar to each other.
    return ChatAnthropic(model=config.MODEL_NAME, temperature=0)
