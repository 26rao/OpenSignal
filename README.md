# OpenSignal

**Self-healing long-tail opportunity monitor for artists, researchers, and creators**

Built for the [Into the Scrape-Verse](https://www.wemakedevs.org/hackathons/scrape-verse) hackathon (WeMakeDevs × Bright Data, 17–23 Aug 2026).

## Problem

Independent artists, researchers, and creators manually check scattered public pages for residencies, open calls, and grants. Those pages change layout often. Ordinary scrapers break quietly. There is no simple, reliable, self-maintaining aggregator for this long tail.

OpenSignal is a practical response to that operational failure mode:
custom Bright Data Scraper Studio collectors, a local quality gate, targeted heal when the gate fails, durable storage, and a dashboard ranked by deadline urgency.

## What works today vs what is still pending

### Done in this repo
- Typed source playbooks and field contracts
- Batch quality gate (scores all records, not one row)
- Heal engine wired to `bdata scraper heal` / `approve`
- Retry on transient CLI failures
- SQLite storage for opportunities and heal events
- CLI operator interface
- Streamlit dashboard with deadline urgency sorting
- Example output schema
- AI disclosure

### Pending until run on your Bright Data account
- Real Collector IDs from Scraper Studio
- At least one live `create` / `run`
- At least one live `heal` / `approve` / re-run
- Real example JSON from a live collector
- Demo video
- Public GitHub submission

## Architecture

```
Bright Data Collector
        │
        ▼
 Quality Gate  ──fail──▶  Heal Engine (`bdata scraper heal`)
        │ pass                    │
        ▼                         ▼
   SQLite store ◀────────── re-run collector
        │
        ▼
 CLI summary / Streamlit dashboard (sorted by deadline urgency)
```

Design choices, briefly:
- Quality gate is local and cheap on purpose. It checks field presence rates across the full batch.
- Bright Data heal is the repair path required by the hackathon and keeps the same `c_*` Collector ID.
- Playbooks are typed so required fields and heal prompts are explicit.
- University and government domains are avoided because Rule 7 bans government sites and public university domains are a gray area.

This architecture is motivated by known failure modes in web extraction research (layout change, brittle wrappers, expensive per-page LLM extraction, weak repair loops). It does **not** claim to implement any paper’s method or “future work” item line-for-line.

## Quick start

1. Create collectors — see `docs/CREATE_SCRAPERS.md`
2. Install:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```
3. Put real `c_*` IDs and API key in `.env`
4. Run:
   ```bash
   python -m opensignal.cli status
   python -m opensignal.cli run --all
   streamlit run src/opensignal/dashboard/app.py
   ```

## How Bright Data Scraper Studio is used

1. `bdata scraper create <url> "<fields>"` → custom collector, stable `c_*` ID
2. `bdata scraper run <id> <url>` → structured JSON
3. Local quality gate scores the batch
4. On failure: `bdata scraper heal <id> "<what broke>"` then `approve`
5. Re-run the **same** collector ID and store results

## Target source (default)

- [Artist Communities Alliance – Open Calls](https://artistcommunities.org/directory/open-calls)

Private residency/open-call directories only. No `.gov` and no university research-office domains.

## Submission checklist

- [ ] Custom Scraper Studio scrapers created on your account
- [ ] Public source-code repository
- [x] Clear README
- [ ] Example structured output from a **live** run (schema sample exists under `data/examples/`)
- [ ] Demo video showing create → run → heal → recovered data
- [x] Explanation of how Bright Data Scraper Studio is used
- [x] AI assistance disclosed in `DISCLOSURE.md`

## License

MIT. Hackathon IP belongs to the participant/team.
