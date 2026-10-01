"""Metrics, split by whether they need ground truth we don't have yet.

Tier 1/2 (below, `NotImplementedError`): need a real pilot case's actual
outcome/citations to compare against. Left failing loudly on purpose rather
than returning a fake number - see docs/EVALUATION.md for the full tier
breakdown.

Cooperation metrics (below that): computable from a rollout alone, no ground
truth needed. These run today, on every episode - see history.py.
"""
import re
from collections import Counter


# --- Evaluation Point 1: task performance (needs ground truth - pending pilot set) ---

def factual_grounding_rate(final_answer: str, shared_facts: list[str]) -> float:
    """% of claims in final_answer traceable to shared_facts."""
    raise NotImplementedError


def citation_accuracy(final_answer: str, ground_truth_citations: list[str]) -> float:
    """Are the cases/statutes cited in final_answer real and on-point."""
    raise NotImplementedError


def outcome_match(final_answer: str, ground_truth_outcome: str) -> float:
    """Did the predicted outcome match the real decision."""
    raise NotImplementedError


# --- Evaluation Point 2: cooperation quality (needs ground truth) ---

def branch_pruning_accuracy(rollout_log: list[dict], correct_branch_id: str) -> float:
    """Did the Critic prune everything except (something that led to) the
    correct branch, without pruning the correct one along the way."""
    raise NotImplementedError


def synthesis_redundancy_retention(final_answer: str, surviving_branches: list[dict]) -> float:
    """Harmonic mean of redundancy (low duplication of source material) and
    retention (how much of the winning branches' substance survived), each
    on a 0-10 LLM-judged scale. Directly adapted from the document-merging
    evaluation in Besta et al., "Graph of Thoughts" (AAAI-24 /
    arXiv:2308.09687) - our Synthesis step IS a document-merging task
    (surviving branches -> one memo), and this metric formalizes exactly
    the over-quoting failure mode we found by eyeballing the 2026-09
    transcript: a memo that's mostly verbatim quotes scores low on
    redundancy even if it scores high on retention, and the harmonic mean
    (unlike an average) punishes that imbalance rather than hiding it.

    Needs an LLM-judge call (their method: query 3x per value, average) -
    not implemented yet, hence the raise. Requires a human-validated judge
    prompt first, per the Tier 2 caution in docs/EVALUATION.md.
    """
    raise NotImplementedError


# --- Computable today: structural cooperation metrics, no ground truth needed ---

_ROLE_TAG = re.compile(r"^\[(.*?)\]\s*(.*)$")


def _gini(values: list[float]) -> float:
    """Standard discrete Gini coefficient. 0 = perfectly even, 1 = fully concentrated."""
    values = [v for v in values if v >= 0]
    if not values or sum(values) == 0:
        return 0.0
    values = sorted(values)
    n = len(values)
    cum = sum((i + 1) * v for i, v in enumerate(values))
    return (2 * cum) / (n * sum(values)) - (n + 1) / n


def _best_matching_role(support_text: str, shared_facts: list[str]) -> str | None:
    """Support strings don't reliably keep the scout's [role] prefix even when
    the prompt asks for a verbatim quote (see the 2026-09 transcript) - so we
    recover it by word-overlap against the tagged shared_facts pool instead of
    assuming an exact match. Heuristic, not exact; documented as such in
    docs/EVALUATION.md.
    """
    support_words = set(support_text.lower().split())
    best_role, best_overlap = None, 0
    for fact in shared_facts:
        m = _ROLE_TAG.match(fact)
        if not m:
            continue
        role, text = m.group(1), m.group(2)
        overlap = len(support_words & set(text.lower().split()))
        if overlap > best_overlap:
            best_role, best_overlap = role, overlap
    return best_role


def branch_support_gini(branches: list[dict], shared_facts: list[str]) -> float:
    """Among non-pruned branches, how concentrated is their cited support
    across scout roles? 0 = draws evenly from multiple sources (real
    cross-source synthesis); close to 1 = leans almost entirely on one
    source's framing. Inspired by the Gini-over-agents metric in the
    zero-cost-collaboration paper (arXiv:2604.07821), applied to source
    attribution instead of task completions.
    """
    all_roles = {m.group(1) for f in shared_facts if (m := _ROLE_TAG.match(f))}
    if len(all_roles) < 2:
        return 0.0  # only one source exists at all - "concentration" isn't a meaningful question

    surviving = [b for b in branches if b["status"] != "pruned"]
    role_counts: Counter = Counter({role: 0 for role in all_roles})  # unused roles must count as 0
    for b in surviving:
        for s in b.get("support", []):
            role = _best_matching_role(s, shared_facts)
            if role:
                role_counts[role] += 1
    if sum(role_counts.values()) == 0:
        return 0.0  # no support matched any role - nothing to measure
    return _gini(list(role_counts.values()))


def branch_diversity(branches: list[dict]) -> float:
    """Did the initial (depth-0, freshly-created) branches actually explore
    different theories, or converge on the same one despite being told to
    diverge? 0 = identical support sets (no real diversity), 1 = fully
    disjoint. Cheap lexical-overlap proxy, not semantic - good enough to
    flag convergence, not to grade argument quality.
    """
    initial = [b for b in branches if b.get("support")]
    if len(initial) < 2:
        return 0.0
    sets = [set(" ".join(b["support"]).lower().split()) for b in initial]
    pairs = [(i, j) for i in range(len(sets)) for j in range(i + 1, len(sets))]
    if not pairs:
        return 0.0
    similarities = []
    for i, j in pairs:
        union = sets[i] | sets[j]
        if not union:
            continue
        similarities.append(len(sets[i] & sets[j]) / len(union))
    if not similarities:
        return 0.0
    return 1.0 - (sum(similarities) / len(similarities))
