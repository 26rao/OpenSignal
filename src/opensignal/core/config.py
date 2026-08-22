"""Typed configuration — constrained playbooks, not free-form scraper code."""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class FieldSpec(BaseModel):
    name: str
    required: bool = True
    description: str = ""


class SourcePlaybook(BaseModel):
    """One reusable collector and its quality contract."""

    name: str
    collector_id: str
    base_url: str
    description: str
    required_fields: List[FieldSpec]
    # {missing} and {fields} are filled by QualityReport.heal_prompt()
    heal_prompt_template: str = (
        "{missing} "
        "Repair the scraper so every output object consistently includes "
        "non-empty {fields} fields when those values exist on the page. "
        "Keep the same output schema and field names."
    )
    quality_threshold: float = 0.85
    enabled: bool = True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bright_data_api_key: str = ""
    open_signal_db_path: str = "./data/opensignal.db"
    log_level: str = "INFO"
    quality_threshold: float = 0.85
    auto_approve_heal: bool = False

    # Filled after you create real collectors in Scraper Studio
    collector_artist_communities: Optional[str] = None
    collector_nyfa: Optional[str] = None


def default_playbooks(settings: Settings) -> Dict[str, SourcePlaybook]:
    """
    Default sources.

    Only private/non-government long-tail directories.
    Rule 7 bans government websites; public university domains are avoided
    as a gray area.

    A source stays disabled until its Collector ID is a real c_* value.
    """
    artist_id = settings.collector_artist_communities or "c_REPLACE_ME"
    nyfa_id = settings.collector_nyfa or "c_REPLACE_ME"

    common_fields = [
        FieldSpec(name="title", required=True, description="Call or residency title"),
        FieldSpec(
            name="deadline",
            required=False,
            description="Application deadline when present on the page",
        ),
        FieldSpec(name="url", required=True, description="Detail or apply URL"),
        FieldSpec(name="location", required=False, description="City/country if present"),
        FieldSpec(name="organization", required=False, description="Host org if present"),
    ]

    return {
        "artist_communities": SourcePlaybook(
            name="artist_communities",
            collector_id=artist_id,
            base_url="https://artistcommunities.org/directory/open-calls",
            description="Artist Communities Alliance open calls and residencies",
            required_fields=common_fields,
            quality_threshold=settings.quality_threshold,
            enabled=artist_id != "c_REPLACE_ME",
        ),
        # Optional second source — enable only after creating a real collector.
        # Browse the board first to confirm cards show title/deadline on the list page.
        "nyfa_opportunities": SourcePlaybook(
            name="nyfa_opportunities",
            collector_id=nyfa_id,
            base_url="https://www.nyfa.org/opportunities/",
            description="NYFA Opportunities Board — open calls, residencies, grants",
            required_fields=common_fields,
            quality_threshold=settings.quality_threshold,
            enabled=nyfa_id != "c_REPLACE_ME",
        ),
    }

settings = Settings()