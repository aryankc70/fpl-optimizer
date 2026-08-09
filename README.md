# FPL Optimizer

A production-grade, season-long Fantasy Premier League decision-support system — combining a trained ML model, integer linear programming, and real football domain knowledge to recommend squads, starting lineups, transfers, and chip timing.

**Live demo:** [fpl-optimizer-kappa.vercel.app](https://fpl-optimizer-kappa.vercel.app)
**API docs:** [fpl-optimizer-api-mdnu.onrender.com/docs](https://fpl-optimizer-api-mdnu.onrender.com/docs)

> Note: the backend runs on a free-tier instance and sleeps after ~15 minutes of inactivity. The first request after idle may take 10–20 seconds to wake up.

---

## What it does

This isn't a static prediction tool — it's a full pipeline that ingests live FPL data, engineers features grounded in football analytics (rolling form, expected goals, Poisson-based clean sheet probability, defensive contribution), trains a LightGBM model to predict player points, and feeds those predictions into an OR-Tools constraint solver that picks a genuinely optimal 15-man squad and starting XI under real FPL rules (budget, position quotas, max-3-per-club). On top of that sit two strategy tools grounded in documented FPL theory: a transfer/hit advisor implementing the "3-week outscore rule," and a season-phase chip-timing calendar.

It runs itself: a scheduled job re-ingests live data, retrains the model, and regenerates predictions automatically as each gameweek finishes.

## Architecture
┌─────────────┐ ┌──────────────┐ ┌─────────────┐
│ React UI │─────▶│ FastAPI │─────▶│ PostgreSQL │
│ (Vercel) │ │      (Render) │      │ (Neon) │
└─────────────┘ └──────┬───────┘ └─────────────┘
│
┌────────┴────────┐
│ LightGBM model │
│ OR-Tools CP-SAT │
└─────────────────┘

Local dev (Docker Compose): Postgres + API + APScheduler container
Production: Neon (DB) + Render (API) + Vercel (frontend) + GitHub Actions (weekly refresh cron)

## Tech stack

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic
- **ML:** LightGBM, pandas, scikit-learn
- **Optimization:** Google OR-Tools (CP-SAT solver)
- **Database:** PostgreSQL
- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **Infra:** Docker, Docker Compose, GitHub Actions CI/CD, APScheduler
- **Deployment:** Neon (DB), Render (API), Vercel (frontend)

## Features

- **Points prediction model** — LightGBM trained on rolling player form (points, minutes, xG, xA, defensive contribution), team defensive strength, and price, beating a naive "recent average" baseline
- **Two-stage ILP optimizer** — first solves optimal 15-man squad selection (budget, position quotas, club limits), then solves starting XI + captain/vice-captain selection as a separate, correctly-scoped problem
- **Poisson clean sheet model** — estimates fixture-specific clean sheet probability from team attack/defense strength ratings, with automatic fallback when granular data isn't yet available (e.g. pre-season)
- **Transfer/hit advisor** — implements the FPL "3-week outscore rule": recommends against a -4 point hit unless the incoming player projects to outscore the outgoing player by 4+ points over the next 3 gameweeks, adjusted for fixture difficulty
- **Chip strategy calendar** — season-phase guidance for Wildcard, Bench Boost, Free Hit, and Triple Captain timing, based on synthesized multi-year FPL strategy analysis
- **Player availability integration** — live injury/suspension status and chance-of-playing percentage discount predictions accordingly, rather than treating every player as guaranteed to start
- **Fully automated weekly refresh** — re-ingests live data, retrains the model, and regenerates predictions for the next unplayed gameweek with no manual intervention

## Notable engineering decisions & bugs solved

A few things worth highlighting, since they reflect genuine debugging rather than a clean first pass:

- **FPL's player IDs are not stable across seasons.** An early version of the historical data backfill matched players by numeric ID across seasons, silently mapping the wrong player's stats onto the wrong current player (confirmed by cross-referencing real 2025-26 season results). Fixed by switching to normalized name-based matching, validated against real season outcomes (e.g. correctly identifying the actual Golden Boot winner).
- **Shrinkage estimation for pre-season predictions.** Early-season "next gameweek" predictions relied on a player's most recent 3-game window — which for most players meant the *end* of last season, a small, noisy sample vulnerable to rotation/dead-rubber distortion. Fixed with an empirical-Bayes-style shrinkage estimator blending recent form with full-season averages, weighted by sample size.
- **A migration that only worked "by accident."** An early Alembic baseline migration was generated against an already-populated local database, so it only recorded incremental changes — it silently failed against a genuinely empty database (like a fresh production deploy). Rebuilt from a truly empty schema to produce a real, standalone-correct baseline.
- **CORS trailing-slash mismatch.** Production frontend-to-backend requests failed silently with no error beyond a generic "Failed to fetch," traced via `curl` to a single trailing slash in the allowed-origins config not matching the browser's `Origin` header exactly.

## Known limitations

Documented honestly rather than hidden:

- Set-piece duty (penalties, corners, free-kicks) isn't modeled — this is scouting/news knowledge, not derivable from statistics, and even professional FPL analysts layer this in manually.
- Historical training data only extends one season back.
- The `value` (price-at-gameweek) field in live in-season ingestion is currently a placeholder — not used by any active feature, but not accurately populated either.
- Blank/double gameweek predictions in the chip calendar are estimates based on historical cup scheduling patterns, not confirmed fixtures.
- No user accounts — the hit advisor evaluates any two players, not a specific user's actual current squad.

## Running locally

**Docker (recommended):**
```bash
cd docker
docker compose up --build
```
This starts Postgres, the FastAPI backend, and the scheduler together. Migrations run automatically on startup.
API: `http://localhost:8000` · Docs: `http://localhost:8000/docs`

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```
`http://localhost:5173`

**Local Python environment (for running ingestion/training scripts directly):**
```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Testing & CI

```bash
pytest tests/ -v
ruff check src/ tests/
```

GitHub Actions runs linting, the test suite, and a Docker build validation on every push to `main`.

## Project structure

fpl-optimizer/
├── src/fpl_optimizer/
│ ├── ingestion/ # FPL API + historical data pipelines
│ ├── features/ # Poisson clean sheet model
│ ├── models/ # dataset building, training, prediction
│ ├── optimization/ # ILP squad/lineup solvers, hit advisor, chip calendar
│ ├── api/ # FastAPI app
│ ├── db/ # SQLAlchemy models, session
│ └── scheduler.py # APScheduler weekly refresh
├── frontend/ # React + TypeScript + Tailwind
├── alembic/ # database migrations
├── tests/ # pytest suite
├── docker/ # Dockerfile, docker-compose.yml
└── .github/workflows/ # CI pipeline

## Author

Built by Aryan — M.S. Computer Science (AI specialization), Utica University.