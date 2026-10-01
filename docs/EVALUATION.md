# Evaluation Framework

**Status:** Living document — expect this to grow as the pilot case set exists and ground-truth-dependent metrics come online.
**Last updated:** October 2026

This is the full breakdown of what we measure, why, and what's actually computable today vs. blocked on the real pilot case set. `BLUEPRINT.md` has the one-paragraph summary; this is the detail that changes fastest.

---

## 1. What we extract at each stage

| Stage | Input | Output | What kind of claim is this? |
|---|---|---|---|
| Scout | One party's/source's raw text slice | `shared_facts`: atomic claims, tagged `[role] fact` | "What was asserted" — no judgment yet |
| Reasoner | All `shared_facts` (+ parent branch if extending) | `Branch`: hypothesis + cited support | "What theory could explain the facts" |
| Critic | All branches + all facts | Per-branch verdict (status, score, reason) + advance/continue | "Which theories survive scrutiny" |
| Synthesis | Surviving branches + facts (never raw text) | `final_answer` memo | "What's the answer, and why" |
| Rollout log | — | Every Critic decision, depth, reason | The trace reward functions read |

The only thing $\pi_\phi$ (blueprint Section 4) will ever control is the Critic's row — which branches survive and when to stop. That constraint shapes the credit-assignment discussion in §6.

---

## 2. Task decomposition

End-to-end task performance is *outcome prediction with a defensible reasoning trace*, but we score the sub-tasks separately because end-to-end accuracy alone can't tell you which of four cooperating agents is responsible for a bad result:

- **Extraction fidelity** (Scout) — real, non-fabricated claims?
- **Hypothesis quality** (Reasoner) — coherent theories, actually grounded in what they cite?
- **Branch judgment** (Critic) — correctly separates sound theories from overreaching ones?
- **Synthesis quality** — does the memo reflect the winning branch(es) honestly?
- **Outcome accuracy** — did the final call match what actually happened?

This decomposition caught a real bug, not a hypothetical one: our first real pilot run (2026-09) produced a good end-to-end answer, but Synthesis complied so literally with "quote specific facts" that the memo became almost entirely stitched verbatim quotes. An end-to-end-only metric would never have surfaced that.

---

## 3. Evaluation tiers

### Tier 1 — automatable, ground-truth-checkable

| Metric | What it checks | Status |
|---|---|---|
| Citation validity | Is a cited case real? (CourtListener's citation-lookup API) | Pending pilot set |
| Citation precision/recall | Does the predicted citation list overlap with what the real court actually cited? | Pending pilot set |
| Outcome match | Did the predicted winner match the real holding? | Pending pilot set — `eval/metrics.py::outcome_match` is a stub |
| Fact fidelity | Does every `shared_facts` entry trace back to the source text? | Pending — `factual_grounding_rate` stub |

Cheap, scales to a large pilot set, no human or judge model needed once the pilot set exists.

### Tier 2 — rubric + LLM-judge, calibration required

- Legal soundness of a hypothesis, independent of whether it won
- Quality of a distinguishing argument
- Synthesis persuasiveness as a memo a real attorney would find credible
- **`synthesis_redundancy_retention`** (new) — harmonic mean of redundancy (low duplication) and retention (how much substance survived), each 0-10, LLM-judged. Adapted directly from the document-merging evaluation in Besta et al.'s *Graph of Thoughts* (AAAI-24) — Synthesis's job (surviving branches → one memo) is structurally the same task they evaluated. This formalizes the over-quoting bug we already found by eyeballing: a quote-stuffed memo would score low redundancy even with high retention, and the harmonic mean punishes that imbalance instead of averaging it away. Stub in `eval/metrics.py`, needs a human-validated judge prompt first (see caution below).

**The catch:** an LLM judge can be fooled by exactly the failure mode we already found. A memo that's 80% verbatim quotes can look "well-supported" to a judge scoring on citation density, when it's actually regurgitation. Any Tier 2 rubric needs a human spot-check pass before it's trusted as a reward signal.

### Tier 3 — genuinely contested

Cases where real lawyers would disagree. Tracked as their own bucket, never averaged into an accuracy number — forcing a scalar here hides the disagreement instead of resolving it.

---

## 4. Cooperation metrics

| Metric | What it measures | Computable today? | Source/inspiration |
|---|---|---|---|
| `branch_support_gini` | Does the winning branch draw evenly from multiple scout sources, or lean on one? 0 = even, →1 = concentrated | **Yes** — `eval/metrics.py` | Gini-over-agents from the zero-cost-collaboration paper (arXiv:2604.07821), applied to source attribution instead of task completions |
| `branch_diversity` | Did initial branches actually explore different theories, or converge despite being told to diverge? | **Yes** — lexical-overlap proxy | Our own transcript: all 3 branches converged on one theory in the first real run |
| Critic reasoning fidelity | Does a verdict's stated `reason` actually describe the branch it's judging, or read like generic pattern-matching? | Not yet — needs a pattern/keyword audit pass, see §6 | Private-thought defection-language analysis, arXiv:2604.07821 §5 |
| Backtrack utility | When a branch is extended, does it genuinely improve, or just restate itself? | Not yet exercised — our first run advanced immediately; needs a case that actually backtracks | — |
| LLM calls per episode | Efficiency — fewer calls to the same answer is better, more calls to a *better* answer may be worth it | **Yes** — `state["llm_call_count"]`, tracked live by every node | Msgs/Task from both papers |
| Branch pruning accuracy | Did the Critic prune everything except what led to the correct branch? | Pending ground truth | `eval/metrics.py::branch_pruning_accuracy` stub |

**On "capability doesn't predict cooperation"** (arXiv:2604.07821's headline finding): a more capable model can cooperate *worse* in a free-cooperation setting than a weaker one. Don't assume upgrading `config.MODEL_NAME` fixes a cooperation-shaped problem like the branch-convergence issue above — test it, the same way that paper had to test it empirically rather than infer it from general capability.

---

## 5. The credit-assignment problem

The reward function in `tot_marl/policy/reward.py` (`R_total = R_task + R_efficiency + R_consensus`) has a real flaw: **`R_task` as "did the final answer match ground truth" is contaminated by things $\pi_\phi$ doesn't control.** If Synthesis writes a bad memo off a correctly-pruned branch, that's not a Critic-policy failure — but a naive reward punishes it as one.

**Borrowed fix — causal decomposition** (arXiv:2604.07821 §4): automate one side of the pipeline at a time to isolate which role is actually the bottleneck.

- **Oracle-Critic ablation**: replace `LLMRouter.decide` with a ground-truth-informed rule (once real cases exist). If output quality jumps, the bottleneck was Critic judgment, not Reasoner hypothesis quality.
- **Auto-Advance ablation**: force "advance" after exactly one pass, bypassing Critic scoring entirely. If scores barely drop, the Critic isn't adding value yet — effort belongs in Reasoner prompts, not Critic prompts.

**Status:** not built yet — needs real ground truth to make "oracle" meaningful. The episode schema (§7) already has a `mode` field (`"baseline"` today) specifically so these ablation runs can share the same history file and get filtered apart later, without a schema migration.

---

## 6. Episode history mechanism

Every `python -m eval.run_pilot` run gets recorded as one line in `eval/history/episodes.jsonl` via `eval/history.py::record_episode`. This is how "is it actually improving" gets answered — by reading trend lines across commits, not by eyeballing one run.

**Why version-controlled, not gitignored:** the point is a persistent record across code/prompt changes. "Did that Synthesis prompt edit help?" is a question about this file's git history.

### Episode schema

```json
{
  "episode_id": "...",
  "timestamp": "...",
  "case_id": "example-001",
  "mode": "baseline",
  "config": {"model": "...", "num_initial_branches": 3, "max_tot_depth": 3, "use_learned_router": false},
  "run_stats": {"depth_reached": 0, "num_branches_final": 3, "num_branches_pruned": 1, "llm_call_count": 8},
  "cooperation_metrics": {"branch_support_gini": 0.67, "branch_diversity": 0.0},
  "ground_truth": null,
  "ground_truth_metrics": null,
  "final_answer": "...",
  "branches": [...],
  "rollout_log": [...]
}
```

`config` is captured per-episode on purpose — without it, a metric change across episodes is ambiguous: did a prompt change, or did someone just bump `MAX_TOT_DEPTH`?

### Reading trends

```bash
python -m eval.report              # every recorded episode, readable table
python -m eval.report example-001  # filtered to one case
```

Prints run stats and cooperation metrics per episode, plus a first-vs-latest comparison once there are 2+ episodes. No plotting library — the pilot set is small enough that a table is genuinely enough for now; revisit if the case set grows past a size where eyeballing stops working.

### Adding ground truth later

Once a pilot case has a real, labeled outcome, pass it to `record_episode(..., ground_truth={...})`. It's stored as-is under `"ground_truth"`; `"ground_truth_metrics"` stays `null` until the Tier 1 functions in `eval/metrics.py` are implemented against it — the schema doesn't need to change when that happens, only the function bodies do.

---

## 7. Known limitations in the metrics themselves

- **`branch_support_gini`'s role-matching is a heuristic, not exact.** Support strings don't reliably retain the `[role]` prefix even when the prompt asks for a verbatim quote (confirmed in the 2026-09 transcript — the model paraphrased slightly). We recover the role via word-overlap against the tagged `shared_facts` pool, which is approximate.
- **`branch_diversity` is lexical, not semantic.** Two branches phrased completely differently but arguing the same underlying theory will score as "diverse" when they aren't. Good enough to flag the convergence case we actually saw; not a substitute for an embedding-based or LLM-judged diversity check later.
- **Gini needs ≥2 known scout roles to mean anything** — with one source, "concentration" isn't a meaningful question, so the metric returns 0 (not an error) in that case.
- **`llm_call_count` counts calls, not tokens.** It's the right efficiency proxy for "is the pipeline doing unnecessary work," but real token-based cost tracking (via LangChain's usage-metadata callbacks) is a future refinement, not built yet.

---

## 8. Status table

| Metric | Tier | Implemented? |
|---|---|---|
| `branch_support_gini` | Cooperation | ✅ Live |
| `branch_diversity` | Cooperation | ✅ Live |
| `llm_call_count` | Efficiency | ✅ Live (tracked in `GraphState`) |
| Episode recording + trend report | Infra | ✅ Live (`eval/history.py`, `eval/report.py`) |
| `factual_grounding_rate` | Tier 1 | ❌ Stub — needs pilot set |
| `citation_accuracy` | Tier 1 | ❌ Stub — needs pilot set |
| `outcome_match` | Tier 1 | ❌ Stub — needs pilot set |
| `branch_pruning_accuracy` | Tier 2/Cooperation | ❌ Stub — needs pilot set |
| `synthesis_redundancy_retention` | Tier 2 | ❌ Stub — needs human-validated judge prompt |
| Critic reasoning-fidelity audit | Cooperation | ❌ Not started |
| Oracle-Critic / Auto-Advance ablations | Credit assignment | ❌ Not started — needs ground truth |
| Token-based `R_efficiency` | Reward | ❌ Not started — call-count proxy used instead |

---

## 9. A metric we're deliberately not adopting yet: volume of a thought

Besta et al. also propose *volume* — for a given thought, the count of upstream thoughts that could have influenced it via a directed path. It's a real, useful concept for telling genuine cross-branch synthesis apart from a thought that only ever saw its own lineage. It's not useful for us **yet**: our pipeline is flat (every Reasoner call sees all of `shared_facts`, Synthesis sees all surviving branches), so every thought's volume is trivially maximal by construction — it can't discriminate anything right now. It becomes a real metric the moment we add a GoT-style aggregate/merge operation (discussed as a future upgrade in an earlier design pass): a merged branch's volume would then meaningfully distinguish "drew on two independent lines of reasoning" from "just extended itself in isolation." Worth revisiting then, not before.

---

## 10. References

- Zhu, K. et al. *MultiAgentBench: Evaluating the Collaboration and Competition of LLM agents.* [arXiv:2503.01935](https://arxiv.org/abs/2503.01935) — Task Score vs. Coordination Score kept separate; iteration-count ablation showing coordination degrades past a point (informed our `MAX_TOT_DEPTH` cap).
- Yadav, A., Black, S., Sourbut, O. *More Capable, Less Cooperative? When LLMs Fail At Zero-Cost Collaboration.* [arXiv:2604.07821](https://arxiv.org/abs/2604.07821) — capability-cooperation inversion; the causal decomposition method behind §5; the Gini-over-agents metric behind `branch_support_gini`.
- Besta, M. et al. *Graph of Thoughts: Solving Elaborate Problems with Large Language Models.* AAAI-24. [DOI:10.1609/aaai.v38i16.29720](https://ojs.aaai.org/index.php/AAAI/article/view/29720) — the redundancy/retention document-merging metric behind `synthesis_redundancy_retention`; the volume-of-a-thought concept (§9 above).
- `BLUEPRINT.md` §4 — the reward function and MARL framework this evaluation layer ultimately feeds.
