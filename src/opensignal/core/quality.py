"""Quality Gate — presence/schema checks across the full batch.

Cheap and deterministic (no LLM). Scores every record, not one row.
Produces a specific heal prompt from field-level evidence so Bright Data
heal can target partial drift instead of rebuilding everything.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .config import SourcePlaybook


@dataclass
class FieldResult:
    name: str
    present_rate: float
    required: bool
    example_value: Any = None
    failing_url: Any = None
    reason: str = ""


@dataclass
class QualityReport:
    source: str
    collector_id: str
    overall_score: float
    passed: bool
    record_count: int
    field_results: List[FieldResult] = field(default_factory=list)
    missing_required: List[str] = field(default_factory=list)
    weak_required: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def heal_prompt(self, playbook: SourcePlaybook) -> str:
        fields_list = ", ".join(
            f.name for f in playbook.required_fields if f.required
        ) or "the required fields"

        if self.record_count == 0:
            missing = (
                "No records were returned at all — the page structure may have "
                "changed entirely."
            )
            return playbook.heal_prompt_template.format(
                missing=missing, fields=fields_list
            )

        problems: List[str] = []

        if self.missing_required:
            problems.append(
                f"These required fields are empty on every one of "
                f"{self.record_count} records: "
                + ", ".join(self.missing_required)
                + "."
            )

        if self.weak_required:
            parts: List[str] = []
            for fr in self.field_results:
                if fr.name not in self.weak_required:
                    continue
                pct = int(fr.present_rate * 100)
                hint = ""
                if fr.example_value is not None:
                    hint = f' (it does work sometimes, e.g. "{fr.example_value}")'
                fail_hint = ""
                if fr.failing_url:
                    fail_hint = (
                        f' Example listing missing this field: {fr.failing_url}'
                    )
                parts.append(
                    f"{fr.name} is present on only {pct}% of records{hint}.{fail_hint}"
                )
            problems.append(
                "These fields are inconsistent across records, which usually means "
                "a selector matches some listing items but not others: "
                + " ".join(parts)
            )

        missing = " ".join(problems) if problems else "Critical fields are unreliable."
        return playbook.heal_prompt_template.format(
            missing=missing, fields=fields_list
        )


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    if text == "" or text.lower() in {"null", "none", "n/a", "na", "-"}:
        return False
    return True


def evaluate(records: List[Dict[str, Any]], playbook: SourcePlaybook) -> QualityReport:
    """Score the full batch.

    overall_score = mean of per-required-field present_rates.
    missing_required: present_rate == 0
    weak_required: 0 < present_rate < threshold
    """
    required_specs = [s for s in playbook.required_fields if s.required]
    optional_specs = [s for s in playbook.required_fields if not s.required]

    if not records:
        return QualityReport(
            source=playbook.name,
            collector_id=playbook.collector_id,
            overall_score=0.0,
            passed=False,
            record_count=0,
            missing_required=[s.name for s in required_specs],
            notes=["No records returned — possible total extraction failure"],
        )

    field_results: List[FieldResult] = []
    missing_required: List[str] = []
    weak_required: List[str] = []
    required_rates: List[float] = []

    for spec in required_specs + optional_specs:
        present_count = 0
        example = None
        failing_url = None
        for r in records:
            if _is_present(r.get(spec.name)):
                present_count += 1
                if example is None:
                    example = r.get(spec.name)
            elif failing_url is None and _is_present(r.get("url")):
                failing_url = r.get("url")

        present_rate = present_count / len(records)
        field_results.append(
            FieldResult(
                name=spec.name,
                present_rate=round(present_rate, 3),
                required=spec.required,
                example_value=example,
                failing_url=failing_url,
                reason=f"{present_count}/{len(records)} records have a non-empty value",
            )
        )
        if spec.required:
            required_rates.append(present_rate)
            if present_rate == 0.0:
                missing_required.append(spec.name)
            elif present_rate < playbook.quality_threshold:
                weak_required.append(spec.name)

    overall = sum(required_rates) / len(required_rates) if required_rates else 0.0
    passed = (
        overall >= playbook.quality_threshold
        and not missing_required
        and not weak_required
    )

    notes: List[str] = []
    if len(records) < 3:
        notes.append(
            f"Low volume: only {len(records)} record(s) — possible partial failure"
        )
    if weak_required:
        notes.append("Partial batch drift on: " + ", ".join(weak_required))

    return QualityReport(
        source=playbook.name,
        collector_id=playbook.collector_id,
        overall_score=round(overall, 3),
        passed=passed,
        record_count=len(records),
        field_results=field_results,
        missing_required=missing_required,
        weak_required=weak_required,
        notes=notes,
    )
