# AI Assistance Disclosure

AI coding assistance was used while developing and scaffolding this repository (project architecture, local deterministic quality gate, test suite, and operator CLI).

### Verified Status & Division of Work:
- **Custom Scraper Studio Collector:** Created and configured by the participant on their Bright Data account (`c_mt4ocq9ano4db5xji` targeting `https://www.nyfa.org/opportunities/`).
- **Live Scraper Execution:** Real CLI scrape executed on the NYFA Opportunities Board, returning 55 structured opportunities preserved in [`data/examples/live_output_res.json`](data/examples/live_output_res.json).
- **Data Integrity:** Raw scraped output reflects exact Scraper Studio extraction (`title`, `location`, `organization`, `url` reliably present; `deadline` sparse on listing cards). No synthetic deadlines have been injected into the scraped data.
- **Self-Healing Verification:** `bdata scraper heal` and `bdata scraper approve` were executed and verified, maintaining the stable collector ID `c_mt4ocq9ano4db5xji`.
- **Quality Gate & Persistence:** Local batch quality scoring, deadline parser/normalizer, and SQLite storage with upsert deduplication are fully implemented and locally tested.
- **Demo Video:** Recorded by the human participant ([YouTube Video Link](https://youtu.be/qVLbth3hI7Q); recording script prepared in [`docs/DEMO.md`](docs/DEMO.md)).

The participant is responsible for all submitted code, scraper configurations, architectural decisions, and final submission materials as required by the hackathon rules.


