# Create the custom Scraper Studio collectors

These steps require your Bright Data account. Library scrapers do not qualify.

## 0. Target Directory Selection

Use private foundations / residency directories / open-call aggregators.

Do **not** use government websites (Rule 7).
Avoid public university research-office domains; they are a gray area under the same rule.

### Primary Verified Target:
- **NYFA Opportunities Board**: `https://www.nyfa.org/opportunities/`
  - Verified active collector: `c_mt4in6dn1s7rasxppn` (configured in `.env` as `COLLECTOR_NYFA`)
  - Directory structure: 24+ structured opportunities per batch with titles, locations, organizations, and application URLs.

*(Note: `artistcommunities.org` was initially tested during exploratory development, but dropped because Scraper Studio was unable to generate a stable template for that domain. NYFA was selected and fully verified as the reliable primary source).*

---

## 1. Login
```bash
npx -p @brightdata/cli bdata login
```

---

## 2. Verified Collector Workflow

### Stage A — Create Collector
```bash
npx -p @brightdata/cli bdata scraper create \
  "https://www.nyfa.org/opportunities/" \
  "Extract opportunity listings as a list of objects with keys: title, url."
```

Set the generated Collector ID in `.env` as `COLLECTOR_NYFA`.

### Stage B — Run Collector
```bash
npx -p @brightdata/cli bdata scraper run c_mt4in6dn1s7rasxppn \
  "https://www.nyfa.org/opportunities/" --pretty
```

### Stage C — Self-Healing / Schema Expansion
```bash
npx -p @brightdata/cli bdata scraper heal c_mt4in6dn1s7rasxppn \
  "Add location and organization fields to each opportunity object. Keep title and url. Return consistent non-empty values when present on the page."

npx -p @brightdata/cli bdata scraper approve c_mt4in6dn1s7rasxppn
```

### Stage D — Re-run Same Collector ID
```bash
npx -p @brightdata/cli bdata scraper run c_mt4in6dn1s7rasxppn \
  "https://www.nyfa.org/opportunities/" --pretty
```

The exact same `c_mt4in6dn1s7rasxppn` collector ID is maintained, data fields are expanded, and downstream orchestrator code runs seamlessly.

