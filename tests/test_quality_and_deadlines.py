"""Local tests — no Bright Data account required."""
from datetime import date

from opensignal.core.config import FieldSpec, SourcePlaybook
from opensignal.core.quality import evaluate
from opensignal.core.deadlines import parse_deadline, sort_by_urgency, days_until


def _playbook() -> SourcePlaybook:
    return SourcePlaybook(
        name="test",
        collector_id="c_test",
        base_url="https://example.com",
        description="test",
        required_fields=[
            FieldSpec(name="title", required=True),
            FieldSpec(name="deadline", required=True),
            FieldSpec(name="url", required=True),
            FieldSpec(name="location", required=False),
        ],
        quality_threshold=0.85,
    )


def test_quality_scores_full_batch_not_first_row_only():
    records = [
        {"title": "A", "deadline": "Sep 10, 2026", "url": "https://example.com/a"},
        {"title": "B", "deadline": None, "url": "https://example.com/b"},
        {"title": "", "deadline": "Sep 11, 2026", "url": "https://example.com/c"},
    ]
    report = evaluate(records, _playbook())
    assert report.record_count == 3
    assert report.passed is False
    assert report.overall_score < 0.85


def test_quality_all_missing():
    report = evaluate([{"title": None}], _playbook())
    assert report.passed is False
    assert "title" in report.missing_required
    assert "deadline" in report.missing_required
    assert "url" in report.missing_required


def test_deadline_urgency_sort():
    records = [
        {"title": "rolling", "deadline": "Rolling"},
        {"title": "later", "deadline": "December 1, 2026"},
        {"title": "sooner", "deadline": "September 1, 2026"},
    ]
    ranked = sort_by_urgency(records)
    assert ranked[0]["title"] == "sooner"
    assert ranked[1]["title"] == "later"
    assert ranked[2]["title"] == "rolling"
    assert parse_deadline("September 10, 2026") == date(2026, 9, 10)
    assert days_until("September 10, 2026", today=date(2026, 9, 1)) == 9


def test_heal_prompt_uses_field_evidence():
    records = [
        {
            "title": "A",
            "deadline": "Sep 10, 2026",
            "url": "https://example.com/a",
            "location": "NY",
        },
        {
            "title": "B",
            "deadline": "Sep 11, 2026",
            "url": "https://example.com/b",
            "location": None,
        },
        {
            "title": "C",
            "deadline": "Sep 12, 2026",
            "url": "https://example.com/c",
            "location": "",
        },
    ]
    # location is optional — force it required for this test via custom playbook
    pb = SourcePlaybook(
        name="test",
        collector_id="c_test",
        base_url="https://example.com",
        description="test",
        required_fields=[
            FieldSpec(name="title", required=True),
            FieldSpec(name="deadline", required=True),
            FieldSpec(name="url", required=True),
            FieldSpec(name="location", required=True),
        ],
        quality_threshold=0.9,
    )
    report = evaluate(records, pb)
    assert "location" in report.weak_required
    prompt = report.heal_prompt(pb)
    assert "location" in prompt
    assert "only" in prompt and "%" in prompt
    assert "title, deadline, url, location" in prompt
    # example of a working value should appear
    assert "NY" in prompt
