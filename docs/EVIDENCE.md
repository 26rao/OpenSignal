# OpenSignal — Bright Data Scraper Studio Evidence Log

This document records the verified live execution, custom collector configuration, and self-healing lifecycle for OpenSignal.

---

## 1. Collector Details

- **Target Source:** NYFA Opportunities Board
- **Target URL:** `https://www.nyfa.org/opportunities/`
- **Collector ID:** `c_mt4in6dn1s7rasxppn`
- **Collector Type:** Custom Scraper Studio Collector (created on participant account)
- **Extracted Fields (Raw Collector):** `title`, `location`, `organization`, `url`, `deadline` (when present on list cards)

---

## 2. Live Scraper Execution & Proof

### Command
```bash
npx -p @brightdata/cli bdata scraper run c_mt4in6dn1s7rasxppn \
  "https://www.nyfa.org/opportunities/" --pretty
```

### Verified Execution Output Summary
- **Response ID:** `d2t1787421744937r0rllu46kdvg`
- **Records Returned:** 24 structured opportunity listings
- **Raw Listing Fields:** `title` (24/24), `location` (24/24), `organization` (24/24), `url` (24/24), `deadline` (1/24 on list card)
- **Raw CLI Artifacts:** Preserved in [`data/examples/live_output_nyfa.json`](../data/examples/live_output_nyfa.json) and [`data/examples/_brightdata_stdout.txt`](../data/examples/_brightdata_stdout.txt)

---

## 3. Self-Healing & Schema Expansion Proof

### Heal Command Sent
```bash
npx -p @brightdata/cli bdata scraper heal c_mt4in6dn1s7rasxppn \
  "Add location and organization fields to each opportunity object. Keep title and url. Return consistent non-empty values when present on the page."
```

### Approval
```bash
npx -p @brightdata/cli bdata scraper approve c_mt4in6dn1s7rasxppn
```

### Post-Heal Re-run on Same Collector ID
```bash
npx -p @brightdata/cli bdata scraper run c_mt4in6dn1s7rasxppn \
  "https://www.nyfa.org/opportunities/" --pretty
```

- **Collector ID Stability:** Maintained stable `c_mt4in6dn1s7rasxppn` ID across creation, healing, and production runs.
- **Lineage:** Recorded in SQLite table `heal_events`.

---

## 4. End-to-End Orchestration & Quality Gate

### Pipeline Execution
```bash
python -m opensignal.cli run nyfa_opportunities
```

### Workflow:
1. **Raw Scrape:** Collector returns 24 opportunities from list view.
2. **Deadline Enrichment:** Python pipeline checks titles and opportunity detail pages for explicit submission deadlines, normalizing valid dates to ISO `YYYY-MM-DD` (`null` when genuinely absent, avoiding fabricated dates).
3. **Batch Quality Gate:** Validates batch completeness against required playbook contracts (`title`, `url`).
4. **SQLite Storage:** Upserts opportunities using `(source, url)` as unique key to prevent duplicates.

### Run Summary Output
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
