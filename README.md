# OpenSignal 📡

[![OpenSignal CI](https://github.com/26rao/OpenSignal/actions/workflows/ci.yml/badge.svg)](https://github.com/26rao/OpenSignal/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hackathon: Into the Scrape-Verse](https://img.shields.io/badge/Hackathon-Into_the_Scrape--Verse-orange.svg)](https://www.wemakedevs.org/hackathons/scrape-verse)

> **Self-healing long-tail opportunity monitor for artists, researchers, and creators.**  
> Built for the **Into the Scrape-Verse** hackathon (WeMakeDevs × Bright Data, August 2026).

---

## 🎯 Problem & Solution

Independent artists, researchers, and creators constantly monitor fragmented public directories for residencies, open calls, grants, and exhibition opportunities. These web pages change layout unpredictably, causing traditional rule-based web scrapers to break silently with empty or corrupted data fields.

**OpenSignal** provides a resilient, self-maintaining extraction pipeline:
1. **Bright Data Scraper Studio collectors** extract structured listing batches from target directories.
2. **Local Batch Quality Gate** evaluates the entire result set against typed schema contracts.
3. **Automated Self-Healing Loop** invokes `bdata scraper heal` with structured diagnostic prompts when quality drops below threshold.
4. **Durable SQLite Storage** logs opportunity history, deduplicates records, and records heal audit events.
5. **Urgency-Ranked Dashboard** surfaces opportunities prioritized by impending deadline deadlines.

---

## 🏗️ Architecture & Data Flow

```
┌────────────────────────────────────────────────────────┐
│             Target Public Opportunity Directory        │
│          (e.g., Artist Communities Alliance, NYFA)     │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │ Bright Data Scraper Studio│ (Collector ID: c_*)
              │      `bdata scraper run`  │
              └─────────────┬─────────────┘
                            │ Structured JSON Batch
                            ▼
              ┌───────────────────────────┐
              │     Batch Quality Gate    │
              │  (Evaluates field rates,  │
              │   missing keys & schemas) │
              └──────┬─────────────┬──────┘
                     │             │
        Quality PASS │             │ Quality FAIL (< 85%)
                     │             ▼
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

- **Typed Source Playbooks**: Declarative definitions in `config.py` specify required/optional fields, base URLs, and target thresholds.
- **Batch Quality Gate**: Validates the *entire* batch output rather than a single sample row to prevent subtle partial data degradation.
- **In-Place Collector Repair**: Uses Bright Data's `heal` and `approve` API, keeping the collector ID (`c_*`) stable without breaking downstream consumer code.
- **Deadline Intelligence & Urgency Scoring**: Normalizes disparate date formats and ranks listings into `Urgent (<7d)`, `Soon (<30d)`, `Open`, and `Rolling`.
- **Operator-Friendly CLI**: Rich terminal tables and structured JSON diagnostics via Typer.
- **Interactive Streamlit Dashboard**: Filter by source, inspect urgency badges, and review self-healing history.
- **Zero Heavy Infra**: SQLite storage with zero external database dependencies for local execution.

---

## 📁 Repository Structure

```
OpenSignal/
├── .github/workflows/
│   └── ci.yml                 # Automated testing and linting CI workflow
├── data/
│   └── examples/              # Verified sample and live collector outputs
│       ├── live_output_res.json # Live run payload from Scraper Studio
│       └── sample_output.json # Baseline schema example
├── docs/
│   ├── CREATE_SCRAPERS.md     # Step-by-step guide to configure Scraper Studio
│   └── DEMO.md                # 90-second video demo walkthrough script
├── src/opensignal/
│   ├── core/
│   │   ├── config.py          # Typed playbooks & Pydantic settings
│   │   ├── deadlines.py       # Date parsing & urgency ranking engine
│   │   ├── orchestrator.py    # Pipeline coordinator (Scrape → Gate → Heal → Store)
│   │   └── quality.py         # Batch quality scoring & repair prompt synthesis
│   ├── dashboard/
│   └── app.py                 # Streamlit visual interface & urgency monitor
│   ├── heal/
│   │   └── engine.py          # Bright Data CLI wrapper for heal/approve/run
│   └── storage/
│       └── db.py              # SQLite storage layer & audit logging
├── tests/
│   └── test_quality_and_deadlines.py # Unit tests for scoring & deadline ranking
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

Update your `.env` with your Bright Data credentials and Collector IDs (see [docs/CREATE_SCRAPERS.md](docs/CREATE_SCRAPERS.md)):

```ini
BRIGHT_DATA_API_KEY=your_bright_data_api_key_here
COLLECTOR_ARTIST_COMMUNITIES=c_YOUR_COLLECTOR_ID
COLLECTOR_NYFA=c_YOUR_COLLECTOR_ID
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

Execute scraping and quality evaluation:
```bash
# Run all enabled sources
python -m opensignal.cli run --all

# Run a specific playbook
python -m opensignal.cli run artist_communities

# Run with forced self-healing pass
python -m opensignal.cli run artist_communities --force-heal
```

### Launch the Streamlit Dashboard

```bash
streamlit run src/opensignal/dashboard/app.py
```

Open `http://localhost:8501` to view ranked opportunities, filter by urgency, and inspect heal events.

---

## 🧪 Testing

OpenSignal includes comprehensive local unit tests for the quality scoring engine and deadline parsing logic that run without requiring Bright Data API calls:

```bash
pytest
```

---

## 🛡️ Hackathon Compliance & Ethics

- **Bright Data Scraper Studio**: Core collector orchestration and healing strictly leverage Bright Data Scraper Studio CLI (`bdata`).
- **Ethical Targets**: Only targets public artist directories (e.g. Artist Communities Alliance, NYFA).
- **Rule 7 Compliance**: Strictly excludes `.gov` and public government research offices.
- **AI Disclosure**: Transparent AI usage disclosure provided in [DISCLOSURE.md](DISCLOSURE.md).

---

## 📜 License

MIT License. Developed for the 2026 **Into the Scrape-Verse** Hackathon.
