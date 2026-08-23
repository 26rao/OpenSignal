# Demo recording script (~90 seconds)

Use the verified NYFA collector flow from `CREATE_SCRAPERS.md`.

## Before you hit record
- [x] Real collector created (`c_mt4ocq9ano4db5xji`)
- [x] `COLLECTOR_NYFA=c_mt4ocq9ano4db5xji` set in `.env`
- [x] Streamlit running: `py -3.13 -m streamlit run src/opensignal/dashboard/app.py`
- [x] Second window/tab ready with the dashboard (`http://localhost:8501`)

## Timeline

| Time | Beat | On screen | Say / caption |
|------|------|-----------|---------------|
| 0:00–0:10 | Problem | Target page (`https://www.nyfa.org/opportunities/`) | "Creators and artists miss career-defining open calls when listing pages change and custom scrapers break quietly." |
| 0:10–0:20 | Collector | `py -3.13 -m opensignal.cli list-sources` showing real `c_*` | "OpenSignal connects a custom Bright Data Scraper Studio collector as a stable production endpoint." |
| 0:20–0:40 | Quality Gate & Fault Injection | `py -3.13 -m opensignal.cli run nyfa_opportunities --simulate-drift` | "We simulate schema drift where organization extraction drops. The OpenSignal quality gate catches the missing field and fails the batch at zero point six six, immediately dispatching a repair request." |
| 0:40–1:00 | Heal & Approve | `bdata scraper heal` + `approve` | "OpenSignal dispatches an evidence-based repair prompt to Bright Data heal on the exact same collector ID. We approve the repair in place without rewriting downstream consumers." |
| 1:00–1:15 | Re-run same ID | `py -3.13 -m opensignal.cli run nyfa_opportunities` → quality report | "On production re-run, quality passes at zero point nine nine, restoring structured organization data and saving fifty-five live opportunities." |
| 1:15–1:30 | Dashboard & Pitch | Cut to Streamlit dashboard (`http://localhost:8501`) & GitHub | "All 55 opportunities feed our urgency dashboard, ranked by genuine deadline proximity without synthetic dates. The collector ID stays the contract; Scraper Studio keeps it alive." |

## Commands Reference

```bash
# Check sources
py -3.13 -m opensignal.cli list-sources

# Controlled drift run (Quality Gate fails on missing:organization)
py -3.13 -m opensignal.cli run nyfa_opportunities --simulate-drift

# Bright Data Self-Healing on same collector ID
npx -p @brightdata/cli bdata scraper heal c_mt4ocq9ano4db5xji \
  "Repair the scraper so every output object includes a non-empty organization field when the organization name is visible on the listing card. Keep title and url unchanged. Same field names. Listing page only."

# Approve repair
npx -p @brightdata/cli bdata scraper approve c_mt4ocq9ano4db5xji

# Full production pipeline run
py -3.13 -m opensignal.cli run nyfa_opportunities
```

