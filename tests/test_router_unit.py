from tot_marl.policy.router import _format_branches


def test_format_branches_excludes_pruned():
    branches = [
        {"branch_id": "b0", "hypothesis": "H0", "support": ["f1"], "status": "active", "score": 0.7},
        {"branch_id": "b1", "hypothesis": "H1", "support": ["f2"], "status": "pruned", "score": 0.1},
    ]
    formatted = _format_branches(branches)
    assert "b0" in formatted
    assert "H0" in formatted
    assert "b1" not in formatted
    assert "H1" not in formatted
