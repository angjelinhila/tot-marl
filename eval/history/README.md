# Episode history

`episodes.jsonl` lives here once the first pilot run creates it (via
`eval/history.py`'s `record_episode`). One JSON object per line, append-only.

This file is **intentionally version-controlled, not gitignored.** The point
of recording episodes isn't just today's run - it's being able to look back
across commits and answer "did that prompt change actually help?" by reading
the file's git history, not by trusting memory.

Read it with:

```bash
python -m eval.report              # all episodes, readable table
python -m eval.report example-001  # filtered to one case
```

See `docs/EVALUATION.md` for what each recorded field means and which
metrics are computable today vs. pending the real pilot case set.
