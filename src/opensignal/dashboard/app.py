"""Streamlit dashboard — opportunities ranked by deadline urgency."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from opensignal.core.config import settings
from opensignal.core.deadlines import days_until, parse_deadline, sort_by_urgency
from opensignal.storage.db import Base, HealEvent, Opportunity, get_engine

st.set_page_config(page_title="OpenSignal", page_icon="📡", layout="wide")
st.title("📡 OpenSignal")
st.caption("Self-healing opportunity monitor for artists and researchers")

engine = get_engine(settings.open_signal_db_path)
Base.metadata.create_all(engine)

with Session(engine) as session:
    opps = session.execute(
        select(Opportunity).order_by(Opportunity.scraped_at.desc()).limit(500)
    ).scalars().all()
    heals = session.execute(
        select(HealEvent).order_by(HealEvent.timestamp.desc()).limit(20)
    ).scalars().all()

records = [
    {
        "title": o.title,
        "deadline": o.deadline,
        "location": o.location,
        "organization": o.organization,
        "url": o.url,
        "source": o.source,
        "quality_score": o.quality_score,
        "scraped_at": o.scraped_at.isoformat() if o.scraped_at else None,
    }
    for o in opps
]
ranked = sort_by_urgency(records)

col1, col2, col3 = st.columns(3)
col1.metric("Opportunities stored", len(records))
col2.metric("Heal events", len(heals))
if ranked:
    top_days = days_until(ranked[0].get("deadline"))
    col3.metric(
        "Next deadline",
        ranked[0]["deadline"] or "Rolling/unknown",
        delta=None if top_days is None else f"in {top_days} days",
    )
else:
    col3.metric("Next deadline", "–")

st.subheader("Opportunities by deadline urgency")
if not ranked:
    st.info("No data yet. Run `python -m opensignal.cli run --all` after configuring collectors.")
else:
    for rec in ranked[:50]:
        dleft = days_until(rec.get("deadline"))
        if dleft is None:
            urgency = "rolling/unknown"
        elif dleft < 0:
            urgency = f"passed ({abs(dleft)}d ago)"
        elif dleft <= 7:
            urgency = f"⚠️ {dleft}d left"
        else:
            urgency = f"{dleft}d left"

        label = f"{rec.get('title') or 'Untitled'} · {rec.get('deadline') or 'no deadline'} · {urgency}"
        with st.expander(label):
            st.write(f"**Source:** {rec.get('source')}")
            st.write(f"**Organization:** {rec.get('organization') or '–'}")
            st.write(f"**Location:** {rec.get('location') or '–'}")
            st.write(f"**URL:** {rec.get('url')}")
            st.write(
                f"**Scraped:** {rec.get('scraped_at')} · Quality: {rec.get('quality_score')}"
            )
            st.write(
                f"**Parsed deadline:** {parse_deadline(rec.get('deadline')) or 'unparsed'}"
            )

st.subheader("Heal history")
if not heals:
    st.write("No heal events yet.")
else:
    for h in heals:
        st.code(
            f"{h.timestamp} | {h.source} | {h.status} | score_before={h.quality_before}\n"
            f"{(h.prompt or '')[:300]}"
        )
