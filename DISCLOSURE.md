# AI Assistance Disclosure

AI coding assistance was used while developing and scaffolding this repository (project structure, test suite, and operator CLI design).

### Verified Status & Division of Work:
- **Custom Scraper Studio Collector:** Created and executed by the participant on their Bright Data account (`c_mt4in6dn1s7rasxppn`).
- **Live Execution & Artifacts:** Real CLI scrape executed on the NYFA Opportunities Board, returning 24 structured opportunities preserved in [`data/examples/live_output_nyfa.json`](data/examples/live_output_nyfa.json).
- **Self-Healing Loop:** Verified with `bdata scraper heal` and `bdata scraper approve` maintaining collector ID `c_mt4in6dn1s7rasxppn`.
- **Quality Gate & Pipeline:** Local deterministic quality checks, deadline parsing/normalization, and SQLite upsert deduplication implemented and tested.
- **Demo Video:** Recorded by the human participant following [`docs/DEMO.md`](docs/DEMO.md) for final submission.

The participant is responsible for all submitted code, scraper configurations, architectural decisions, and final submission materials as required by the hackathon rules.

