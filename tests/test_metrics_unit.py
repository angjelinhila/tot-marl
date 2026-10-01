from eval.metrics import _gini, branch_diversity, branch_support_gini


def test_gini_even_split_is_zero():
    assert _gini([5, 5, 5]) == 0.0


def test_gini_single_value_is_zero():
    # Degenerate case: Gini needs >=2 values to express inequality at all.
    # branch_support_gini guards against this by requiring >=2 known roles
    # before calling _gini - see test below.
    assert _gini([3]) == 0.0


def test_gini_fully_concentrated_is_high():
    g = _gini([10, 0, 0])
    assert g > 0.6


SHARED_FACTS = [
    "[plaintiff_facts] Plaintiff claims breach.",
    "[defendant_facts] Defendant claims extension.",
    "[prior_case_law] Court held extension can modify terms.",
]


def test_branch_support_gini_one_source_only_is_high():
    # All cited support traces back to a single scout role, despite three
    # roles existing - this should score as HIGH concentration (close to 1),
    # not zero, because the other two roles were available and ignored.
    branches = [{
        "branch_id": "b0",
        "status": "active",
        "support": ["Plaintiff claims breach.", "Plaintiff claims breach again."],
    }]
    gini = branch_support_gini(branches, SHARED_FACTS)
    assert gini > 0.5


def test_branch_support_gini_even_draw_is_low():
    branches = [{
        "branch_id": "b0",
        "status": "active",
        "support": [
            "Plaintiff claims breach.",
            "Defendant claims extension.",
            "Court held extension can modify terms.",
        ],
    }]
    gini = branch_support_gini(branches, SHARED_FACTS)
    assert gini < 0.2


def test_branch_diversity_identical_branches_is_zero():
    branches = [
        {"branch_id": "b0", "support": ["same fact one", "same fact two"]},
        {"branch_id": "b1", "support": ["same fact one", "same fact two"]},
    ]
    assert branch_diversity(branches) == 0.0


def test_branch_diversity_disjoint_branches_is_high():
    branches = [
        {"branch_id": "b0", "support": ["alpha beta gamma"]},
        {"branch_id": "b1", "support": ["delta epsilon zeta"]},
    ]
    assert branch_diversity(branches) == 1.0
