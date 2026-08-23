# OpenSignal — Bright Data Scraper Studio Evidence Log

This document provides a factual record of the live execution, custom collector configuration, and self-healing lifecycle for OpenSignal.

---

## 1. Collector Configuration

- **Primary Source:** NYFA Opportunities Board
- **Target URL:** `https://www.nyfa.org/opportunities/`
- **Collector ID:** `c_mt4ocq9ano4db5xji`
- **Collector Type:** Custom Scraper Studio Collector created on participant account

---

## 2. Execution Stages & What the Data Proves

### A. Baseline Scraper Run
```bash
npx -p @brightdata/cli bdata scraper run c_mt4ocq9ano4db5xji \
  "https://www.nyfa.org/opportunities/" --pretty
```
- **Records Returned:** 55 structured opportunity listings from NYFA
- **Raw CLI Artifact:** Preserved in [`data/examples/live_output_res.json`](../data/examples/live_output_res.json) and [`data/examples/_brightdata_stdout.txt`](../data/examples/_brightdata_stdout.txt)

### B. Self-Healing & Repair Operation
```bash
# Diagnostic heal prompt submitted to Scraper Studio
npx -p @brightdata/cli bdata scraper heal c_mt4ocq9ano4db5xji \
  "Repair the scraper so every output object includes a non-empty organization field when the organization name is visible on the listing card. Keep title and url unchanged. Same field names. Listing page only."

# Approve repair
npx -p @brightdata/cli bdata scraper approve c_mt4ocq9ano4db5xji
```

### C. Post-Heal Re-run on Same Collector ID
```bash
py -3.13 -m opensignal.cli run nyfa_opportunities
```
- **Collector ID Stability:** The scraper runs on the exact same `c_mt4ocq9ano4db5xji` collector ID across repair and production execution without breaking downstream code.
- **Outcome:** The live run returns `title`, `location`, `organization`, and `url`; listing-card deadlines remain sparse on the board view, which the downstream pipeline handles cleanly without fabrication.
- **Audit Lineage:** Heal events are recorded in SQLite `heal_events` table and `data/heal_history/`.

### D. What the Current Live JSON Actually Proves:
1. **Reliable Listing Fields:** `title`, `location`, `organization`, and `url` are consistently extracted from the listing cards.
2. **Deadline Sparsity on List View:** Explicit deadlines are sparse on the listing view. The raw listing JSON does **not** fabricate missing deadlines.
3. **No Fabricated Deadlines:** In accordance with data integrity rules, unlisted deadlines are left as `null` in the data rather than being synthetic or guessed.
4. **Quality Gate & Persistence:** The local Python pipeline inspects titles and opportunity text for explicit submission dates, normalizes valid dates to ISO `YYYY-MM-DD`, evaluates quality contracts (`title`, `url`, `organization`), and saves verified records to SQLite.

### E. Controlled Drift & Self-Healing Verification (Break → Fail → Heal → Pass)

> **Controlled drift test:** Evaluated controlled schema drift where `organization` was stripped, confirmed deterministic quality failure (`0.661`), invoked `bdata scraper heal` on the same ID, re-ran in production, and recovered `organization` at `0.988` without creating a new collector. Artifacts: [`data/examples/heal_proof/01_baseline.json`](../data/examples/heal_proof/01_baseline.json), [`data/examples/heal_proof/02_broken.json`](../data/examples/heal_proof/02_broken.json), [`data/examples/heal_proof/03_after_heal.json`](../data/examples/heal_proof/03_after_heal.json).

#### Proof Artifacts & Stage Metrics:
1. **`01_baseline.json`** — Healthy live run:
   - `title`: 100%, `url`: 100%, `organization`: 100%, `location`: 100%
   - Quality score: `1.0` (Passed)
2. **`02_broken.json`** — Simulating schema drift / broken extraction:
   - `organization` mapping disabled / stripped in batch
   - Quality score: `0.661` (Failed quality gate threshold `0.85`)
   - Missing required: `['organization']`
   - Generated Heal Prompt:
     ```text
     These required fields are empty on every one of 55 records: organization. Repair the scraper so every output object consistently includes non-empty title, url, organization fields when those values exist on the page. Keep the same output schema and field names.
     ```
3. **`03_after_heal.json`** — Post-repair on exact same collector ID:
   - Scraper validated via Bright Data Scraper Studio & approved (`bdata scraper approve c_mt4ocq9ano4db5xji`)
   - `organization` restored to 100%
   - Quality score: `0.988` / `1.0` (Passed)
   - Audit Lineage: Persisted to `heal_events` table and `data/heal_history/`.

---

## 3. End-to-End CLI Pipeline Run

```bash
py -3.13 -m opensignal.cli run nyfa_opportunities
```

```text
                      OpenSignal Run Summary                      
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Source             ┃ Status ┃ Quality ┃ Records ┃ Missing/Weak ┃
┡━━━━━━━━━━━━━━━━━━━━┇━━━━━━━━┇━━━━━━━━━┇━━━━━━━━━┇━━━━━━━━━━━━━━┩
│ nyfa_opportunities │ ok     │ 0.988   │ 55      │              │
└────────────────────┴────────┴─────────┴─────────┴──────────────┘
[
  {
    "source": "nyfa_opportunities",
    "collector_id": "c_mt4ocq9ano4db5xji",
    "status": "ok",
    "records_fetched": 55,
    "quality_score": 0.988,
    "passed": true,
    "missing": [],
    "weak": [],
    "record_count_scored": 55,
    "saved": 55
  }
]
```
*(Note: Quality score 0.988 reflects high presence of required playbook contract fields `title`, `url`, and `organization`).*

---

## 4. Submission Status

- **Code & Test Suite:** Completed (all 9 unit tests pass).
- **Live Scraper Studio Collector:** Verified on participant account (`c_mt4ocq9ano4db5xji`).
- **Raw Output Artifacts:** Committed in [`data/examples/live_output_res.json`](../data/examples/live_output_res.json) and [`data/examples/heal_proof/`](../data/examples/heal_proof/).
- **Demo Video:** Recorded following [`docs/DEMO.md`](docs/DEMO.md).
