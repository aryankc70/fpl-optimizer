# FPL Optimizer

Season-long Fantasy Premier League points prediction and squad optimization system.
Built with FastAPI, PostgreSQL, and a linear optimization solver.

## Status
🚧 In active development — Step 1: scaffolding





## Setup (Docker — recommended)

```bash
cd docker
docker compose up --build
```

This starts Postgres and the FastAPI app together. Migrations run automatically on startup.
API available at http://localhost:8000, interactive docs at http://localhost:8000/docs.






## Setup
uv venv && source .venv/bin/activate && uv pip install -e ".[dev]"