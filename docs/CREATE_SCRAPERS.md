# Create the custom Scraper Studio collectors

These steps require your Bright Data account. Library scrapers do not qualify.

## 0. Target Directory Selection

Use private foundations / residency directories / open-call aggregators.

Do **not** use government websites (Rule 7).
Avoid public university research-office domains; they are a gray area under the same rule.

### Primary Verified Target:
- **NYFA Opportunities Board**: `https://www.nyfa.org/opportunities/`
  - Verified active collector: `c_mt4ocq9ano4db5xji` (configured in `.env` as `COLLECTOR_NYFA`)
  - Directory structure: 55 structured opportunities per batch with titles, locations, organizations, and application URLs.

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
npx -p @brightdata/cli bdata scraper run c_mt4ocq9ano4db5xji \
  "https://www.nyfa.org/opportunities/" --pretty
```

### Stage C — Self-Healing / Schema Expansion
```bash
npx -p @brightdata/cli bdata scraper heal c_mt4ocq9ano4db5xji \
  "Repair the scraper so every output object includes a non-empty organization field when the organization name is visible on the listing card. Keep title and url unchanged. Same field names. Listing page only."

npx -p @brightdata/cli bdata scraper approve c_mt4ocq9ano4db5xji
```

### Stage D — Re-run Same Collector ID
```bash
npx -p @brightdata/cli bdata scraper run c_mt4ocq9ano4db5xji \
  "https://www.nyfa.org/opportunities/" --pretty
```

The exact same `c_mt4ocq9ano4db5xji` collector ID is maintained, data fields are expanded, and downstream orchestrator code runs seamlessly.

