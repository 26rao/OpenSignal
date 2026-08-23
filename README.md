# OpenSignal 📡

[![OpenSignal CI](https://github.com/26rao/OpenSignal/actions/workflows/ci.yml/badge.svg)](https://github.com/26rao/OpenSignal/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hackathon: Into the Scrape-Verse](https://img.shields.io/badge/Hackathon-Into_the_Scrape--Verse-orange.svg)](https://www.wemakedevs.org/hackathons/scrape-verse)

> **Self-healing long-tail opportunity monitor for artists, researchers, and creators.**  
> Built for the **Into the Scrape-Verse** hackathon (WeMakeDevs × Bright Data, August 2026).  
> 📹 **Demo Walkthrough Script:** [`docs/DEMO.md`](docs/DEMO.md)

---

## 🎯 Problem & Solution

Independent artists, researchers, and creators constantly monitor fragmented public directories for residencies, open calls, grants, and exhibition opportunities. These web pages change layout unpredictably, causing traditional scrapers to break quietly with missing or corrupted fields.

**OpenSignal** provides a resilient, self-maintaining extraction pipeline:
1. **Bright Data Scraper Studio Custom Collector** (`c_mt4ocq9ano4db5xji`) extracts structured batches from the **NYFA Opportunities Board** (`title`, `location`, `organization`, `url`, and card deadlines).
2. **Batch Quality Gate** validates field presence rates across the entire output batch against typed contracts.
3. **Automated Self-Healing Loop** synthesizes targeted repair prompts and calls `bdata scraper heal` + `approve`, maintaining the exact same collector ID.
4. **Deadline Intelligence & Normalization** extracts and normalizes explicit application deadlines from listing text to ISO `YYYY-MM-DD` (or `null` when genuinely unavailable), avoiding fabricated dates.
5. **Durable SQLite Storage** automatically deduplicates/upserts opportunities by `(source, url)` and records heal audit events.
6. **Urgency-Ranked Dashboard** prioritizes opportunities by impending deadlines (`⚠️ Urgent (<7d)`, `Soon (<30d)`, `Open`, `Rolling`).

---

## 🎯 Primary Target Directory

- **Primary Source:** [NYFA Opportunities Board](https://www.nyfa.org/opportunities/)
- **Collector ID:** `c_mt4ocq9ano4db5xji` (configured in `.env` as `COLLECTOR_NYFA`)
- **Verified Raw Output:** 55 structured opportunities per batch (`title`, `organization`, `location`, `url`, and listing `deadline` when present on card).
- **Deadline Intelligence & Normalization:** Listing extraction covers title, url, organization, and location reliably. Explicit deadlines are sparse on the listing view; when absent, we store `null` and never invent synthetic dates. Urgency ranking uses parsed deadlines when present.
- **Quality Gate Score:** 0.988 / 1.0 (High-confidence presence of required playbook contract fields `title`, `url`, and `organization`).
- **Target Selection Note:** Private residency and arts directories only. Strictly excludes `.gov` and public university domains (Hackathon Rule 7).

---

## 🏗️ Architecture & Data Flow

```
┌────────────────────────────────────────────────────────┐
│             Target Public Opportunity Directory        │
│          NYFA Opportunities (nyfa.org/opportunities)   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │ Bright Data Scraper Studio│ (Collector ID: c_mt4ocq9ano4db5xji)
              │      `bdata scraper run`  │
              └─────────────┬─────────────┘
                            │ Structured JSON Batch (55 records)
                            ▼
              ┌───────────────────────────┐
              │    Deadline Intelligence  │ (Extracts & normalizes ISO YYYY-MM-DD
              │       & Enrichment        │  dates from listings; null if none)
              └─────────────┬─────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │     Batch Quality Gate    │
              │  (Evaluates field rates,  │
              │   missing keys & schemas) │
              └──────┬─────────────┬──────┘
                     │             │
        Quality PASS │             │ Quality FAIL (< 85%)
       (Score: 0.99) │             ▼
                     │   ┌───────────────────────────┐
                     │   │   Automated Heal Engine   │
                     │   │   `bdata scraper heal`    │
                     │   │  (Injects repair prompt)  │
                     │   └─────────────┬─────────────┘
                     │                 │
                     │                 ▼
                     │   ┌───────────────────────────┐
                     │   │   `bdata scraper approve` │
                     │   │ (Retries same c_* target) │
                     │   └─────────────┬─────────────┘
                     │                 │
                     ▼                 ▼
              ┌───────────────────────────┐
              │    SQLite Durable Store   │
              │   • Upsert / Deduplication│
              │   • Opportunities Table   │
              │   • Heal Audit Events Log │
              └─────────────┬─────────────┘
                            │
             ┌──────────────┴──────────────┐
             ▼                             ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   Terminal Operator CLI  │  │   Streamlit Web UI       │
│ • `opensignal run`       │  │ • Urgency Badges         │
│ • `opensignal status`    │  │ • Days-to-Deadline sort  │
│ • `opensignal list`      │  │ • Heal Audit Viewer      │
└──────────────────────────┘  └──────────────────────────┘
```

---

## ✨ Key Features

- **Custom Scraper Studio Collector**: Real collector `c_mt4ocq9ano4db5xji` tailored for long-tail arts and creator opportunities.
- **Batch Quality Gate**: Scores the entire batch rather than a single sample row to prevent silent extraction degradation.
- **In-Place Collector Repair**: Uses Bright Data's `heal` and `approve` API, keeping the collector ID (`c_*`) stable without breaking downstream consumer code.
- **Deadline Intelligence & Normalization**: Extracts explicit application deadlines, normalizes them to ISO `YYYY-MM-DD`, and ranks listings into `Urgent (<7d)`, `Soon (<30d)`, `Open`, and `Rolling`. Missing deadlines are cleanly marked as `null` without fabricating data.
- **Deduplication & Storage**: Built-in SQLite upsert logic via `(source, url)` prevents duplicate rows across repeated scraper runs while updating latest dates.
- **Operator-Friendly CLI**: Rich terminal tables and structured JSON diagnostics via Typer.
- **Interactive Streamlit Dashboard**: Filter by source, inspect urgency badges, and review self-healing history.
- **Zero Heavy Infra**: SQLite storage with portable Node/npx path detection across Windows, macOS, and Linux.

---

## 📁 Repository Structure

```
OpenSignal/
├── .github/workflows/
│   └── ci.yml                 # Automated testing and linting CI workflow
├── data/
│   └── examples/              # Verified sample and live collector outputs
│       ├── live_output_nyfa.json # Clean raw CLI payload from Scraper Studio
│       ├── live_output_res.json # Live record payload from Scraper Studio
│       ├── _brightdata_stdout.txt # Live polling & stdout logs from Bright Data run
│       └── heal_proof/        # Baseline, broken & healed lifecycle artifacts
├── docs/
│   ├── CREATE_SCRAPERS.md     # Step-by-step guide to configure Scraper Studio
│   ├── DEMO.md                # 90-second video demo walkthrough script
│   └── EVIDENCE.md            # Live run and self-healing execution proof
├── src/opensignal/
│   ├── core/
│   │   ├── config.py          # Typed playbooks & Pydantic settings
│   │   ├── deadlines.py       # Date parsing, normalization & urgency ranking
│   │   ├── orchestrator.py    # Pipeline coordinator (Scrape → Gate → Heal → Store)
│   │   └── quality.py         # Batch quality scoring & repair prompt synthesis
│   ├── dashboard/
│   │   └── app.py             # Streamlit visual interface & urgency monitor
│   ├── heal/
│   │   └── engine.py          # Bright Data CLI wrapper for heal/approve/run
│   └── storage/
│       └── db.py              # SQLite storage layer & upsert deduplication
├── tests/
│   └── test_quality_and_deadlines.py # Unit tests for scoring, dates & storage
├── DISCLOSURE.md              # AI assistance declaration
├── pyproject.toml             # Project metadata & pytest configuration
└── requirements.txt           # Python dependencies
```

---

## 🚀 Quick Start

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/26rao/OpenSignal.git
cd OpenSignal

# Create and activate virtual environment
python -m venv .venv
# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Update your `.env` with your Bright Data credentials and Collector ID (see [docs/CREATE_SCRAPERS.md](docs/CREATE_SCRAPERS.md)):

```ini
BRIGHT_DATA_API_KEY=your_bright_data_api_key_here
COLLECTOR_NYFA=c_mt4ocq9ano4db5xji
QUALITY_THRESHOLD=0.85
AUTO_APPROVE_HEAL=false
```

---

## 💻 Usage & Commands

### CLI Commands

Check configured playbooks and local status:
```bash
python -m opensignal.cli status
python -m opensignal.cli list-sources
```

Execute scraping, deadline enrichment, and quality evaluation:
```bash
# Run the primary NYFA collector (evaluates live batch & saves to SQLite)
python -m opensignal.cli run nyfa_opportunities

# Run with controlled schema drift simulation (e.g. for testing quality gate failure)
python -m opensignal.cli run nyfa_opportunities --simulate-drift

# Run all enabled sources
python -m opensignal.cli run --all
```

### Launch the Streamlit Dashboard

```bash
streamlit run src/opensignal/dashboard/app.py
```

Open `http://localhost:8501` to view ranked opportunities, filter by urgency, and inspect heal events.

---

## 🧪 Testing

OpenSignal includes comprehensive local unit tests covering quality gate evaluation, deadline normalization, title extraction, and SQLite upsert deduplication:

```bash
pytest
```

---

## 🛡️ Hackathon Compliance & Ethics

- **Bright Data Scraper Studio**: Core collector orchestration and healing strictly leverage Bright Data Scraper Studio CLI (`bdata`).
- **Live Evidence**: Documented in [`docs/EVIDENCE.md`](docs/EVIDENCE.md) with raw output in [`data/examples/live_output_nyfa.json`](data/examples/live_output_nyfa.json).
- **Ethical Targets**: Only targets public artist directories (NYFA Opportunities Board).
- **Rule 7 Compliance**: Strictly excludes `.gov` and public government research offices.
- **AI Disclosure**: Transparent AI usage disclosure provided in [DISCLOSURE.md](DISCLOSURE.md).

---

## 📋 Submission Checklist

- [x] Custom Scraper Studio scraper created on participant account (`c_mt4ocq9ano4db5xji`)
- [x] Public source-code repository
- [x] Accurate & comprehensive README
- [x] Clean structured output from a **live** run ([`data/examples/live_output_nyfa.json`](data/examples/live_output_nyfa.json))
- [x] Documented self-healing execution & evidence ([`docs/EVIDENCE.md`](docs/EVIDENCE.md))
- [x] Explanation of how Bright Data Scraper Studio is used
- [x] AI assistance disclosed in [`DISCLOSURE.md`](DISCLOSURE.md)
- [x] Demo video recording following [`docs/DEMO.md`](docs/DEMO.md)

---

## 📜 License

MIT License. Developed for the 2026 **Into the Scrape-Verse** Hackathon.

