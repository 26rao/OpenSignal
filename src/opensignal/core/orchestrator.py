"""Orchestrator — closed loop: run → validate → heal → re-verify → store.

Design pressure from recent work on reusable extractors and constrained repair:

- Prefer a stable Collector ID over regenerating scrapers.
- Validate before healing.
- Heal with a specific field-failure description, not a vague prompt.
- Keep execution deterministic where possible; escalate to Bright Data heal only on failure.
"""

from __future__ import annotations
import os 
import json
import logging
import subprocess
from typing import Any, Dict, List, Optional

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from opensignal.core.config import SourcePlaybook, Settings, default_playbooks
from opensignal.core.deadlines import enrich_opportunity_deadlines
from opensignal.core.quality import evaluate
from opensignal.heal.engine import HealEngine
from opensignal.storage.db import init_db, save_opportunities, save_heal_event


logger = logging.getLogger(__name__)


def _resolve_npx_cmd() -> List[str]:
    """Resolve npx across PATH and Windows default installation locations."""
    import shutil
    import sys

    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if npx:
        return [npx]
    if sys.platform.startswith("win"):
        for path in [
            r"C:\Program Files\nodejs\npx.cmd",
            r"C:\Program Files (x86)\nodejs\npx.cmd",
        ]:
            if os.path.exists(path):
                return [path]
    return ["npx"]


class CollectorCLIError(RuntimeError):
    """Raised when the Bright Data CLI invocation fails transiently or hard."""


class Orchestrator:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()

        self.playbooks = {
            name: pb
            for name, pb in default_playbooks(self.settings).items()
            if pb.enabled
        }

        self.heal_engine = HealEngine(
            auto_approve=self.settings.auto_approve_heal
        )

        self.Session = init_db(
            self.settings.open_signal_db_path
        )

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(CollectorCLIError),
    )
    def _run_collector(
        self,
        collector_id: str,
        url: str,
    ) -> List[Dict[str, Any]]:
        """Run one Bright Data collector and parse structured output.

        Retries only on CLI/transport failures, not on empty-but-successful
        responses. Empty successful output is treated as a quality failure so
        the heal path can run instead of being confused with a network blip.
        """

        if not collector_id or collector_id == "c_REPLACE_ME":
            raise ValueError(
                f"Collector ID is not configured for this source. "
                f"Create it in Scraper Studio and set it in .env "
                f"(got: {collector_id!r})."
            )

        cmd = _resolve_npx_cmd() + [
            "-p",
            "@brightdata/cli",
            "bdata",
            "scraper",
            "run",
            collector_id,
            url,
            "--pretty",
        ]

        logger.info(
            "Running collector %s on %s",
            collector_id,
            url,
        )

        env = dict(os.environ)
        if self.settings.bright_data_api_key:
            env["BRIGHT_DATA_API_KEY"] = self.settings.bright_data_api_key
            env["BRIGHTDATA_API_KEY"] = self.settings.bright_data_api_key

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
                encoding="utf-8",
                errors="replace",
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            raise CollectorCLIError(
                f"CLI timed out for {collector_id}"
            ) from exc
        except OSError as exc:
            raise CollectorCLIError(
                f"CLI could not start: {exc}"
            ) from exc

        if result.returncode != 0:
            # Nonzero exit is often transient network/auth — retry.
            raise CollectorCLIError(
                f"Collector CLI failed "
                f"(code={result.returncode}): "
                f"{result.stderr[-500:]}"
            )

        text = result.stdout.strip()

        if not text:
            logger.warning(
                "Collector returned empty stdout for %s",
                collector_id,
            )
            return []

        try:
            data = json.loads(text)

        except json.JSONDecodeError:
            # Real CLI output may include logs around JSON.
            # Try to locate the outermost JSON array/object.
            data = self._extract_json_blob(text)

            if data is None:
                logger.warning(
                    "Could not parse CLI output as JSON for %s. "
                    "Raw tail: %s",
                    collector_id,
                    text[-500:],
                )
                return []

        # ------------------------------------------------------------
        # Bright Data output handling
        #
        # The NYFA scraper returns:
        #
        # [
        #   {
        #     "opportunities": [
        #       {...},
        #       {...}
        #     ],
        #     "input": {...}
        #   }
        # ]
        #
        # We need to return the inner opportunities list, not the
        # outer wrapper as one record.
        # ------------------------------------------------------------

        if isinstance(data, list):

            # Bright Data wrapper:
            # [{"opportunities": [...], "input": {...}}]
            if (
                len(data) == 1
                and isinstance(data[0], dict)
                and isinstance(data[0].get("opportunities"), list)
            ):
                opportunities = data[0]["opportunities"]

                logger.info(
                    "Unwrapped %d opportunities from Bright Data response",
                    len(opportunities),
                )

                return opportunities

            return data

        if isinstance(data, dict):

            # Direct opportunities wrapper:
            # {"opportunities": [...]}
            if isinstance(data.get("opportunities"), list):
                opportunities = data["opportunities"]

                logger.info(
                    "Unwrapped %d opportunities from Bright Data response",
                    len(opportunities),
                )

                return opportunities

            # Generic data wrapper:
            # {"data": [...]}
            if isinstance(data.get("data"), list):
                return data["data"]

            # Single record.
            return [data]

        return []

    @staticmethod
    def _extract_json_blob(text: str) -> Any:
        """Best-effort extraction when CLI wraps JSON with log lines."""

        for opener, closer in (
            ("[", "]"),
            ("{", "}"),
        ):
            start = text.find(opener)
            end = text.rfind(closer)

            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(
                        text[start : end + 1]
                    )
                except json.JSONDecodeError:
                    continue

        return None

    def run_one(
        self,
        name: str,
        force_heal: bool = False,
    ) -> Dict[str, Any]:

        if name not in self.playbooks:
            raise ValueError(
                f"Unknown or disabled source: {name}. "
                f"Enabled: {list(self.playbooks.keys())}"
            )

        playbook = self.playbooks[name]

        summary: Dict[str, Any] = {
            "source": name,
            "collector_id": playbook.collector_id,
            "status": "started",
        }

        records = self._run_collector(
            playbook.collector_id,
            playbook.base_url,
        )

        summary["records_fetched"] = len(records)
        records = enrich_opportunity_deadlines(records)

        report = evaluate(
            records,
            playbook,
        )

        summary["quality_score"] = report.overall_score
        summary["passed"] = report.passed
        summary["missing"] = report.missing_required
        summary["weak"] = report.weak_required
        summary["record_count_scored"] = report.record_count

        if report.passed and not force_heal:
            with self.Session() as session:
                saved = save_opportunities(
                    session,
                    name,
                    playbook.collector_id,
                    records,
                    report.overall_score,
                )

            summary["status"] = "ok"
            summary["saved"] = saved

            return summary

        logger.warning(
            "Quality gate failed for %s "
            "(score=%.2f, missing=%s, weak=%s)",
            name,
            report.overall_score,
            report.missing_required,
            report.weak_required,
        )

        heal_event = self.heal_engine.heal(
            playbook,
            report,
        )

        summary["heal"] = {
            "status": heal_event.get("status"),
            "prompt": heal_event.get("heal_prompt"),
        }

        with self.Session() as session:
            save_heal_event(
                session,
                heal_event,
            )

        if heal_event.get("status") == "approved" or (
            heal_event.get("status") == "pending_manual_approve"
            and self.settings.auto_approve_heal
        ):

            records2 = self._run_collector(
                playbook.collector_id,
                playbook.base_url,
            )
            records2 = enrich_opportunity_deadlines(records2)

            report2 = evaluate(
                records2,
                playbook,
            )

            summary["quality_after"] = report2.overall_score
            summary["records_after"] = len(records2)

            if report2.passed:
                with self.Session() as session:
                    saved = save_opportunities(
                        session,
                        name,
                        playbook.collector_id,
                        records2,
                        report2.overall_score,
                    )

                summary["status"] = "healed_and_saved"
                summary["saved"] = saved

            else:
                summary["status"] = "healed_but_still_failing"

        elif heal_event.get("status") == "pending_manual_approve":
            summary["status"] = "heal_pending_manual_approve"

        else:
            summary["status"] = "heal_failed"

        return summary

    def run_all(
        self,
        force_heal: bool = False,
    ) -> List[Dict[str, Any]]:

        results: List[Dict[str, Any]] = []

        if not self.playbooks:
            logger.error(
                "No enabled playbooks. Create collectors in Scraper Studio "
                "and set COLLECTOR_* values in .env"
            )

            return [
                {
                    "source": None,
                    "status": "error",
                    "error": (
                        "No enabled playbooks — configure "
                        "Collector IDs in .env"
                    ),
                }
            ]

        for name in self.playbooks:
            try:
                results.append(
                    self.run_one(
                        name,
                        force_heal=force_heal,
                    )
                )

            except Exception as e:
                logger.exception(
                    "Failed on %s",
                    name,
                )

                results.append(
                    {
                        "source": name,
                        "status": "error",
                        "error": str(e),
                    }
                )

        return results