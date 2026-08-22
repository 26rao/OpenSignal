# Demo recording script (~90 seconds)

Use the verified NYFA collector flow from `CREATE_SCRAPERS.md`. Rehearse once before recording.

## Before you hit record
- [ ] Real collector created (`c_mt4in6dn1s7rasxppn`)
- [ ] `COLLECTOR_NYFA=c_mt4in6dn1s7rasxppn` set in `.env`
- [ ] Terminal font ~16–18pt, dark theme, notifications off
- [ ] `npx` pre-warmed (run any `bdata` command once)
- [ ] Streamlit already running: `streamlit run src/opensignal/dashboard/app.py`
- [ ] Second window/tab ready with the dashboard

## Timeline

| Time | Beat | On screen | Say / caption |
|------|------|-----------|---------------|
| 0:00–0:10 | Pain | Target page (`https://www.nyfa.org/opportunities/`) | "Artists, researchers, and creators manually check fragmented boards for deadlines." |
| 0:10–0:20 | Collector exists | `python -m opensignal.cli list-sources` showing real `c_*` | "Custom Bright Data Scraper Studio collector configured." |
| 0:20–0:35 | Minimal run | `bdata scraper run c_mt4in6dn1s7rasxppn <url> --pretty` → structured batch | "Collects opportunities reliably from the live target." |
| 0:35–1:00 | **Heal (hero)** | Full heal command + approve in real time | "Bright Data self-heals the scraper without changing the collector ID." |
| 1:00–1:15 | Re-run same ID | `python -m opensignal.cli run nyfa_opportunities` → quality 1.0, 24 records | "Same collector ID. Schema enriched. Passed batch quality gate." |
| 1:15–1:30 | Product | Cut to Streamlit dashboard, urgency badges visible | "Ranked by deadline urgency so nothing critical is buried." |

## Commands to keep in a paste buffer

```bash
# Check status and sources
python -m opensignal.cli status
python -m opensignal.cli list-sources

# Live collector run
npx -p @brightdata/cli bdata scraper run c_mt4in6dn1s7rasxppn \
  "https://www.nyfa.org/opportunities/" --pretty

# Bright Data Self-Healing
npx -p @brightdata/cli bdata scraper heal c_mt4in6dn1s7rasxppn \
  "Add location and organization fields to each opportunity object. Keep title and url. Return consistent non-empty values when present on the page."

# Approve repair
npx -p @brightdata/cli bdata scraper approve c_mt4in6dn1s7rasxppn

# Full pipeline run with Quality Gate & Storage
python -m opensignal.cli run nyfa_opportunities
```

