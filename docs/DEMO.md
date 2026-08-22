# Demo recording script (~90 seconds)

Use the staged heal flow from `CREATE_SCRAPERS.md`. Rehearse once before recording.

## Before you hit record
- [ ] Real collector created (Stage A done)
- [ ] `COLLECTOR_ARTIST_COMMUNITIES` set in `.env`
- [ ] Terminal font ~16–18pt, dark theme, notifications off
- [ ] `npx` pre-warmed (run any `bdata` command once)
- [ ] Streamlit already running: `streamlit run src/opensignal/dashboard/app.py`
- [ ] Second window/tab ready with the dashboard

## Timeline

| Time | Beat | On screen | Say / caption |
|------|------|-----------|---------------|
| 0:00–0:10 | Pain | Target page briefly | "Artists and researchers manually check pages like this every week for deadlines." |
| 0:10–0:20 | Collector exists | `python -m opensignal.cli list-sources` showing real `c_*` | "Custom Scraper Studio collector, already created." |
| 0:20–0:35 | Minimal run | `bdata scraper run c_ID <url> --pretty` → title + deadline only | "It works with a minimal schema." |
| 0:35–1:00 | **Heal (hero)** | Full heal command + approve, real time, no cuts | Read the heal prompt briefly; "same Collector ID stays." |
| 1:00–1:15 | Re-run same ID | `bdata scraper run` again → 5 fields | "Same collector ID. Wider schema. Downstream code unchanged." |
| 1:15–1:30 | Product | Cut to Streamlit, urgency badges visible | "Ranked by deadline urgency so nothing critical is buried." |

## Commands to keep in a paste buffer

```bash
python -m opensignal.cli list-sources

npx -p @brightdata/cli bdata scraper run c_YOUR_ID \
  "https://artistcommunities.org/directory/open-calls" --pretty

npx -p @brightdata/cli bdata scraper heal c_YOUR_ID \
  "Add location, organization, and url fields to each listing object. Keep title and deadline. Return consistent non-empty values when present on the page."

npx -p @brightdata/cli bdata scraper approve c_YOUR_ID

npx -p @brightdata/cli bdata scraper run c_YOUR_ID \
  "https://artistcommunities.org/directory/open-calls" --pretty
```

Or drive the full local loop after collectors exist:

```bash
python -m opensignal.cli run artist_communities --force-heal
```
