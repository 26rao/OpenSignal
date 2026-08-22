"""Heal Engine — recovery via Bright Data Scraper Studio CLI.

Bright Data heal is the authoritative repair path required by the hackathon.
This module only decides *when* to call it and *what prompt* to send, then
records the event for audit/lineage.
"""
from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from opensignal.core.config import SourcePlaybook
from opensignal.core.quality import QualityReport

logger = logging.getLogger(__name__)


class HealCLIError(RuntimeError):
    pass


class HealEngine:
    def __init__(
        self,
        auto_approve: bool = False,
        history_dir: Path = Path("data/heal_history"),
    ):
        self.auto_approve = auto_approve
        self.history_dir = history_dir
        self.history_dir.mkdir(parents=True, exist_ok=True)

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(HealCLIError),
    )
    def _run_cli(self, args: List[str]) -> subprocess.CompletedProcess:
        cmd = ["npx", "-p", "@brightdata/cli", "bdata"] + args
        logger.info("Running: %s", " ".join(cmd))
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired as exc:
            raise HealCLIError(f"CLI timed out: {args}") from exc
        except OSError as exc:
            raise HealCLIError(f"CLI could not start: {exc}") from exc
        return result

    def heal(self, playbook: SourcePlaybook, report: QualityReport) -> Dict[str, Any]:
        prompt = report.heal_prompt(playbook)
        event: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": playbook.name,
            "collector_id": playbook.collector_id,
            "quality_before": report.overall_score,
            "missing_fields": report.missing_required,
            "weak_fields": report.weak_required,
            "record_count": report.record_count,
            "heal_prompt": prompt,
            "status": "initiated",
        }

        try:
            result = self._run_cli(["scraper", "heal", playbook.collector_id, prompt])
        except HealCLIError as exc:
            event["status"] = "heal_failed"
            event["error"] = str(exc)
            self._persist(event)
            return event

        event["heal_stdout"] = (result.stdout or "")[-2000:]
        event["heal_stderr"] = (result.stderr or "")[-1000:]
        event["heal_returncode"] = result.returncode

        if result.returncode != 0:
            event["status"] = "heal_failed"
            self._persist(event)
            return event

        if self.auto_approve:
            approve = self._run_cli(["scraper", "approve", playbook.collector_id])
            event["approve_returncode"] = approve.returncode
            event["status"] = (
                "approved" if approve.returncode == 0 else "approve_failed"
            )
        else:
            event["status"] = "pending_manual_approve"
            event["note"] = (
                "Run manually: npx -p @brightdata/cli bdata scraper approve "
                f"{playbook.collector_id}"
            )

        self._persist(event)
        return event

    def _persist(self, event: Dict[str, Any]) -> None:
        stamp = event["timestamp"].replace(":", "-")
        path = self.history_dir / f"{event['source']}_{stamp}.json"
        path.write_text(json.dumps(event, indent=2))
        logger.info("Heal event persisted → %s", path)
