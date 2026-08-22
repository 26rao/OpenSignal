# OpenSignal — Bright Data Scraper Studio Evidence Log

This document provides a factual record of the live execution, custom collector configuration, and self-healing lifecycle for OpenSignal.

---

## 1. Collector Configuration

- **Primary Source:** NYFA Opportunities Board
- **Target URL:** `https://www.nyfa.org/opportunities/`
- **Collector ID:** `c_mt4in6dn1s7rasxppn`
- **Collector Type:** Custom Scraper Studio Collector created on participant account

---

## 2. Execution Stages & What the Data Proves

### A. Baseline Scraper Run
```bash
npx -p @brightdata/cli bdata scraper run c_mt4in6dn1s7rasxppn \
  "https://www.nyfa.org/opportunities/" --pretty
```
- **CLI Response ID:** `d2t1787421744937r0rllu46kdvg`
- **Records Returned:** 24 structured opportunity listings
- **Raw CLI Artifact:** Preserved in [`data/examples/live_output_res.json`](../data/examples/live_output_res.json) and [`data/examples/_brightdata_stdout.txt`](../data/examples/_brightdata_stdout.txt)

### B. Self-Healing & Repair Operation
```bash
# Diagnostic heal prompt submitted to Scraper Studio
npx -p @brightdata/cli bdata scraper heal c_mt4in6dn1s7rasxppn \
  "On listing cards, capture deadline date when visible. Keep title, location, organization, and url. Maintain consistent schema."

# Approve repair
npx -p @brightdata/cli bdata scraper approve c_mt4in6dn1s7rasxppn
```

### C. Post-Heal Re-run on Same Collector ID
```bash
npx -p @brightdata/cli bdata scraper run c_mt4in6dn1s7rasxppn \
  "https://www.nyfa.org/opportunities/" --pretty
```
- **Collector ID Stability:** The scraper continues to run on the exact same `c_mt4in6dn1s7rasxppn` collector ID across repair and production execution without breaking downstream code.
- **Outcome:** The live list view consistently returns `title`, `location`, `organization`, and `url`; listing-card deadlines remain sparse (~1/24) on the board view, which the downstream pipeline handles cleanly without fabrication.
- **Audit Lineage:** Heal events are recorded in SQLite `heal_events` table.

### D. What the Current Live JSON Actually Proves:
1. **Reliable Listing Fields:** `title` (24/24), `location` (24/24), `organization` (24/24), and `url` (24/24) are consistently extracted from the listing cards.
2. **Deadline Sparsity on List View:** `deadline` is present on approximately 1 listing card (`Annual Members Exhibition... / Deadline 9/15/2026`). The raw listing JSON does **not** prove full-batch deadline coverage from the listing page alone.
3. **No Fabricated Deadlines:** In accordance with data integrity rules, unlisted deadlines are left as `null` in the raw data rather than being synthetic or guessed.
4. **Pipeline Enrichment & Quality Gate:** The local Python pipeline inspects titles and opportunity detail pages for explicit submission dates, normalizes valid dates to ISO `YYYY-MM-DD`, and evaluates quality contracts (`title`, `url` required=True).

---

## 3. End-to-End CLI Pipeline Run

```bash
python -m opensignal.cli run nyfa_opportunities
```

```
                      OpenSignal Run Summary                      
+----------------------------------------------------------------+
| Source             | Status | Quality | Records | Missing/Weak |
|--------------------+--------+---------+---------+--------------|
| nyfa_opportunities | ok     | 1.0     | 24      |              |
+----------------------------------------------------------------+
[
  {
    "source": "nyfa_opportunities",
    "collector_id": "c_mt4in6dn1s7rasxppn",
    "status": "ok",
    "records_fetched": 24,
    "quality_score": 1.0,
    "passed": true,
    "missing": [],
    "weak": [],
    "record_count_scored": 24,
    "saved": 24
  }
]
```
*(Note: Quality score 1.0 reflects 100% presence of the required playbook contract fields `title` and `url`).*

---

## 4. Submission Status

- **Code & Test Suite:** Completed (all 9 unit tests pass).
- **Live Scraper Studio Collector:** Verified on participant account (`c_mt4in6dn1s7rasxppn`).
- **Raw Output Artifacts:** Committed in [`data/examples/live_output_res.json`](../data/examples/live_output_res.json).
- **Demo Video:** **Not yet recorded / pending recording by participant** following [`docs/DEMO.md`](DEMO.md).
