"""Simple durable store for opportunities + heal lineage."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
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
    url = Column(String(1024))
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


def init_db(db_path: str = "./data/opensignal.db") -> sessionmaker:
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def save_opportunities(
    session: Session,
    source: str,
    collector_id: str,
    records: List[Dict[str, Any]],
    quality_score: float,
) -> int:
    count = 0
    for r in records:
        opp = Opportunity(
            source=source,
            collector_id=collector_id,
            title=str(r.get("title") or "")[:512],
            deadline=str(r.get("deadline") or "")[:128] or None,
            location=str(r.get("location") or "")[:256] or None,
            url=str(r.get("url") or "")[:1024],
            organization=str(r.get("organization") or "")[:256] or None,
            raw_json=json.dumps(r),
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
