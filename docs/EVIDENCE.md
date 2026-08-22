# OpenSignal — Bright Data Scraper Studio Evidence Log

This document records the verified live execution, custom collector configuration, and self-healing lifecycle for OpenSignal.

---

## 1. Collector Details

- **Target Source:** NYFA Opportunities Board
- **Target URL:** `https://www.nyfa.org/opportunities/`
- **Collector ID:** `c_mt4in6dn1s7rasxppn`
- **Collector Type:** Custom Scraper Studio Collector (created on participant account)
- **Extracted Fields:** `title`, `url`, `location`, `organization`, `deadline`

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
- **Raw CLI Artifact:** Preserved in [`data/examples/live_output_res.json`](../data/examples/live_output_res.json) and [`data/examples/_brightdata_stdout.txt`](../data/examples/_brightdata_stdout.txt)

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

### Command
```bash
python -m opensignal.cli run nyfa_opportunities
```

### Run Output
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

### Database Persistence
- **Storage:** SQLite (`data/opensignal.db`)
- **Upsert / Deduplication:** Guaranteed unique across runs via `(source, url)` key.
- **Deadline Intelligence:** Normalized ISO `YYYY-MM-DD` dates with urgency ranking surfaced in Streamlit UI.
