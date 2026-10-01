"""Round-trip test for episode recording. Monkeypatches HISTORY_PATH to a
temp file so test runs never pollute the real eval/history/episodes.jsonl -
that file's whole point is a real, version-controlled record, not test noise.
"""
from eval import history as H

FAKE_RESULT = {
    "case_id": "test-case",
    "depth": 1,
    "shared_facts": ["[role_a] fact one"],
    "branches": [
        {"branch_id": "b0", "status": "active", "score": 0.8, "hypothesis": "H", "support": ["fact one"]},
    ],
    "rollout_log": [{"depth": 0, "action": "advance", "reason": "r"}],
    "final_answer": "answer text",
    "llm_call_count": 5,
}


def test_record_and_load_roundtrip(tmp_path, monkeypatch):
    fake_path = tmp_path / "episodes.jsonl"
    monkeypatch.setattr(H, "HISTORY_PATH", fake_path)

    episode = H.record_episode(
        case_id="test-case",
        result=FAKE_RESULT,
        config={"model": "test-model"},
    )

    assert fake_path.exists()
    loaded = H.load_history()
    assert len(loaded) == 1
    assert loaded[0]["episode_id"] == episode["episode_id"]
    assert loaded[0]["case_id"] == "test-case"
    assert loaded[0]["run_stats"]["llm_call_count"] == 5


def test_load_history_empty_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(H, "HISTORY_PATH", tmp_path / "does_not_exist.jsonl")
    assert H.load_history() == []
