"""Print how metrics have moved across recorded episodes. No plotting
library, no dashboard - just a readable table, since the pilot set is small
enough that eyeballing a trend is genuinely enough for now.

    python -m eval.report
    python -m eval.report example-001       # filter to one case
"""
import sys

from .history import load_history


def main(case_filter: str = None) -> None:
    episodes = load_history()
    if case_filter:
        episodes = [e for e in episodes if e["case_id"] == case_filter]

    if not episodes:
        print("No recorded episodes yet - run `python -m eval.run_pilot` first.")
        return

    header = (
        f"{'episode':<10} {'when':<20} {'case_id':<16} {'mode':<10} "
        f"{'depth':<6} {'pruned':<7} {'calls':<6} {'gini':<6} {'diversity':<9}"
    )
    print(header)
    print("-" * len(header))
    for e in episodes:
        rs = e["run_stats"]
        cm = e["cooperation_metrics"]
        calls = rs["llm_call_count"] if rs["llm_call_count"] is not None else "-"
        print(
            f"{e['episode_id']:<10} {e['timestamp'][:19]:<20} {e['case_id']:<16} {e['mode']:<10} "
            f"{rs['depth_reached']:<6} {rs['num_branches_pruned']:<7} {str(calls):<6} "
            f"{cm['branch_support_gini']:<6.2f} {cm['branch_diversity']:<9.2f}"
        )

    if len(episodes) >= 2:
        first, last = episodes[0], episodes[-1]
        print("\nFirst -> latest, same ordering as above:")
        for label, key_path in [
            ("llm_call_count", ("run_stats", "llm_call_count")),
            ("branch_support_gini", ("cooperation_metrics", "branch_support_gini")),
            ("branch_diversity", ("cooperation_metrics", "branch_diversity")),
        ]:
            f_val = first[key_path[0]][key_path[1]]
            l_val = last[key_path[0]][key_path[1]]
            print(f"  {label}: {f_val} -> {l_val}")


if __name__ == "__main__":
    main(*sys.argv[1:])
