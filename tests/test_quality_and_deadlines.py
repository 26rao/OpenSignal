"""Local tests — no Bright Data account required."""
from datetime import date
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from opensignal.core.config import FieldSpec, SourcePlaybook
from opensignal.core.quality import evaluate
from opensignal.core.deadlines import (
    parse_deadline,
    normalize_deadline,
    extract_deadline_from_text,
    enrich_opportunity_deadlines,
    sort_by_urgency,
    days_until,
)
from opensignal.storage.db import Base, Opportunity, save_opportunities, cleanup_duplicates


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


def test_normalize_deadline():
    assert normalize_deadline("September 15, 2026") == "2026-09-15"
    assert normalize_deadline("9/15/2026") == "2026-09-15"
    assert normalize_deadline("09/01/2026") == "2026-09-01"
    assert normalize_deadline("2026-10-23") == "2026-10-23"
    assert normalize_deadline("Rolling") is None
    assert normalize_deadline(None) is None
    assert normalize_deadline("") is None


def test_extract_deadline_from_title_and_text():
    title1 = (
        "Annual Members Exhibition - Juror: Antonia Pocock, Curatorial Assistant, "
        "/ Whitney Museum of Art / Deadline 9/15/2026"
    )
    assert extract_deadline_from_text(title1) == "2026-09-15"

    html_snippet = '<div class="conditionLine calendar">Application Deadline: 09/01/2026</div>'
    assert extract_deadline_from_text(html_snippet) == "2026-09-01"

    text2 = "Submission Deadline: October 15, 2026"
    assert extract_deadline_from_text(text2) == "2026-10-15"

    text3 = "Closes: 11/30/2026 for all applicants."
    assert extract_deadline_from_text(text3) == "2026-11-30"

    text_none = "Art Worker Artist Grant 2026 without any date"
    assert extract_deadline_from_text(text_none) is None


def test_enrich_opportunity_deadlines():
    raw_batch = [
        {
            "title": "Exhibition / Deadline 9/15/2026",
            "url": "https://example.com/opp1",
        },
        {
            "title": "Open Residency",
            "deadline": "September 20, 2026",
            "url": "https://example.com/opp2",
        },
        {
            "title": "Rolling Grant",
            "url": "http://invalid-non-existent-url-domain-12345.org",
        },
    ]

    enriched = enrich_opportunity_deadlines(raw_batch, max_workers=2)
    assert len(enriched) == 3

    # Schema guarantee
    for item in enriched:
        assert "title" in item
        assert "deadline" in item
        assert "location" in item
        assert "organization" in item
        assert "url" in item

    assert enriched[0]["deadline"] == "2026-09-15"
    assert enriched[1]["deadline"] == "2026-09-20"
    assert enriched[2]["deadline"] is None


def test_storage_upsert_deduplication():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    records = [
        {
            "title": "Residency A",
            "url": "https://example.com/a",
            "deadline": "2026-09-01",
            "location": "NY",
            "organization": "Org A",
        },
        {
            "title": "Residency B",
            "url": "https://example.com/b",
            "deadline": "2026-09-15",
            "location": "CA",
            "organization": "Org B",
        },
    ]

    with Session(engine) as session:
        # First save: 2 items
        count1 = save_opportunities(session, "test_source", "c_test", records, 1.0)
        assert count1 == 2
        total = session.query(Opportunity).count()
        assert total == 2

        # Second save with same URLs (and an updated deadline for B)
        updated_records = [
            {
                "title": "Residency A",
                "url": "https://example.com/a",
                "deadline": "2026-09-01",
                "location": "NY",
                "organization": "Org A",
            },
            {
                "title": "Residency B (Extended)",
                "url": "https://example.com/b",
                "deadline": "2026-09-30",
                "location": "CA",
                "organization": "Org B",
            },
        ]
        count2 = save_opportunities(session, "test_source", "c_test", updated_records, 1.0)
        assert count2 == 2

        # Total rows must remain 2, not 4!
        total_after = session.query(Opportunity).count()
        assert total_after == 2

        # Verify update took effect
        opp_b = session.execute(
            select(Opportunity).where(Opportunity.url == "https://example.com/b")
        ).scalar_one()
        assert opp_b.title == "Residency B (Extended)"
        assert opp_b.deadline == "2026-09-30"


def test_storage_cleanup_duplicates():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Manually add duplicate rows
        opp1 = Opportunity(source="src", url="https://example.com/1", title="Opp 1")
        opp2 = Opportunity(source="src", url="https://example.com/1", title="Opp 1 Duplicate")
        session.add_all([opp1, opp2])
        session.commit()
        assert session.query(Opportunity).count() == 2

        # Run cleanup
        removed = cleanup_duplicates(session)
        assert removed == 1
        assert session.query(Opportunity).count() == 1


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
    assert "NY" in prompt

