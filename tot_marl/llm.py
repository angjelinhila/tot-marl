"""Single place every node gets its model client from. Swap models, add
retry/rate-limit handling, or point at a different provider here - nothing
else in the codebase should construct a ChatAnthropic directly.
"""
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

from . import config

load_dotenv()  # picks up ANTHROPIC_API_KEY from a local .env, if present


def get_llm() -> ChatAnthropic:
    # default_headers: works around a decompression bug in httpx2 2.13.1
    # (the anthropic SDK's HTTP layer) - every compressed response hits a
    # TypeError regardless of the algorithm negotiated. Asking the server for
    # an uncompressed body sidesteps the buggy code path entirely. Safe to
    # remove once a fixed httpx2/anthropic release is out.
    #
    # No temperature param: Claude Sonnet 5 (and later models) dropped
    # temperature/top_p/top_k entirely - passing any of them is a 400, not a
    # no-op. Determinism-style control on this model line comes from the
    # thinking/effort settings instead, not sampling temperature.
    return ChatAnthropic(
        model=config.MODEL_NAME,
        default_headers={"Accept-Encoding": "identity"},
    )
