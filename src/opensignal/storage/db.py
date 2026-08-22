"""Simple durable store for opportunities + heal lineage."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


class Opportunity(Base):
    __tablename__ = "opportunities"
    id = Column(Integer, primary_key=True)
    source = Column(String(64), index=True)
    collector_id = Column(String(64))
    title = Column(String(512))
    deadline = Column(String(128), nullable=True)
    location = Column(String(256), nullable=True)
    url = Column(String(1024), index=True)
    organization = Column(String(256), nullable=True)
    raw_json = Column(Text)
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    quality_score = Column(Float, default=1.0)


class HealEvent(Base):
    __tablename__ = "heal_events"
    id = Column(Integer, primary_key=True)
    source = Column(String(64))
    collector_id = Column(String(64))
    timestamp = Column(DateTime)
    quality_before = Column(Float)
    status = Column(String(64))
    prompt = Column(Text)
    details = Column(Text)


def get_engine(db_path: str = "./data/opensignal.db"):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", echo=False)


def cleanup_duplicates(session: Session) -> int:
    """Consolidate historical duplicate records, keeping the most recent."""
    all_opps = session.execute(
        select(Opportunity).order_by(Opportunity.id.desc())
    ).scalars().all()

    seen = set()
    removed = 0
    for opp in all_opps:
        key = (opp.source, opp.url) if opp.url else (opp.source, opp.title)
        if key in seen:
            session.delete(opp)
            removed += 1
        else:
            seen.add(key)
    if removed:
        session.commit()
    return removed


def init_db(db_path: str = "./data/opensignal.db") -> sessionmaker:
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    sm = sessionmaker(bind=engine)
    with sm() as session:
        cleanup_duplicates(session)
    return sm


def save_opportunities(
    session: Session,
    source: str,
    collector_id: str,
    records: List[Dict[str, Any]],
    quality_score: float,
) -> int:
    """Upsert opportunities into database.

    Uses (source, url) as unique identifier to prevent duplicate entries
    across runs while keeping fields, normalized deadlines, and timestamps up to date.
    """
    now = datetime.now(timezone.utc)
    count = 0
    for r in records:
        url_val = str(r.get("url") or "").strip()
        title_val = str(r.get("title") or "").strip()[:512]
        deadline_val = str(r.get("deadline") or "").strip()[:128] or None
        location_val = str(r.get("location") or "").strip()[:256] or None
        org_val = str(r.get("organization") or "").strip()[:256] or None

        existing = None
        if url_val:
            existing = session.execute(
                select(Opportunity).where(
                    Opportunity.source == source,
                    Opportunity.url == url_val,
                )
            ).scalars().first()
            if not existing:
                existing = session.execute(
                    select(Opportunity).where(Opportunity.url == url_val)
                ).scalars().first()
        elif title_val:
            existing = session.execute(
                select(Opportunity).where(
                    Opportunity.source == source,
                    Opportunity.title == title_val,
                )
            ).scalars().first()

        if existing:
            existing.source = source
            existing.collector_id = collector_id
            existing.title = title_val
            existing.deadline = deadline_val
            existing.location = location_val
            existing.organization = org_val
            if url_val:
                existing.url = url_val[:1024]
            existing.raw_json = json.dumps(r)
            existing.scraped_at = now
            existing.quality_score = quality_score
        else:
            opp = Opportunity(
                source=source,
                collector_id=collector_id,
                title=title_val,
                deadline=deadline_val,
                location=location_val,
                url=url_val[:1024] if url_val else "",
                organization=org_val,
                raw_json=json.dumps(r),
                scraped_at=now,
                quality_score=quality_score,
            )
            session.add(opp)
        count += 1

    session.commit()
    return count


def save_heal_event(session: Session, event: Dict[str, Any]) -> None:
    he = HealEvent(
        source=event.get("source"),
        collector_id=event.get("collector_id"),
        timestamp=datetime.fromisoformat(event["timestamp"]),
        quality_before=event.get("quality_before"),
        status=event.get("status"),
        prompt=event.get("heal_prompt"),
        details=json.dumps(event),
    )
    session.add(he)
    session.commit()

