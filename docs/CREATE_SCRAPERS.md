# Create the custom Scraper Studio collectors

These steps require your Bright Data account. Library scrapers do not qualify.

## 0. Prefer long-tail public pages

Use private foundations / residency directories / open-call aggregators.

Do **not** use government websites (Rule 7).
Avoid public university research-office domains; they are a gray area under the same rule.

Default target:
- https://artistcommunities.org/directory/open-calls

## 1. Login
```bash
npx -p @brightdata/cli bdata login
```

## 2. Staged create (recommended for a repeatable heal demo)

Start minimal so you can demonstrate heal by expanding fields.

### Stage A — two fields only
```bash
npx -p @brightdata/cli bdata scraper create \
  "https://artistcommunities.org/directory/open-calls" \
  "Extract open call listings as a list of objects with keys: title, deadline."
```

Copy the returned Collector ID into `.env` as `COLLECTOR_ARTIST_COMMUNITIES`.

### Stage B — run once
```bash
npx -p @brightdata/cli bdata scraper run c_YOUR_ID \
  "https://artistcommunities.org/directory/open-calls" --pretty
```

Save that JSON as `data/examples/live_output.json` for submission.

### Stage C — heal to add fields (demo beat)
```bash
npx -p @brightdata/cli bdata scraper heal c_YOUR_ID \
  "Add location, organization, and url fields to each listing object. Keep title and deadline. Return consistent non-empty values when present on the page."

npx -p @brightdata/cli bdata scraper approve c_YOUR_ID
```

### Stage D — re-run same Collector ID
```bash
npx -p @brightdata/cli bdata scraper run c_YOUR_ID \
  "https://artistcommunities.org/directory/open-calls" --pretty
```

Same `c_*`, wider schema, no downstream rewrite.

## 3. Optional second source

Only add another playbook after you have a real listing URL and a real collector ID.
Do not point a collector at a blog homepage and expect opportunity fields back.
