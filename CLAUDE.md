# The History Atlas — Claude Guide

A web application storing scholarly citations correlating historical people with time and place, presented as an interactive map searchable by time period, geographic area, or person.

## Architecture

| Layer | Tech |
|-------|------|
| Frontend | React 17 / TypeScript in `/client` |
| Backend | Python FastAPI in `/server` |
| Database | PostgreSQL 16 via SQLAlchemy + Alembic |
| Maps | Leaflet / react-leaflet |
| Infra | Docker Compose |

**Main branch:** `main`

## Project Layout

```
/client          React/TypeScript SPA
/server          FastAPI Python backend
  the_history_atlas/
    api/         REST routes and handlers
    apps/        Domain modules (accounts, history, database, config)
    main.py      FastAPI entry point
  tests/         pytest suite
  alembic/       DB migrations
/wikidata        Wikidata API integration service
/wiki_link       Wikipedia link processing service
/test_provisioner Docker service for test DB setup
/scripts         Utility scripts (story ordering, tracing)
```

## Running Tests

**Backend** (requires Docker):
```bash
docker compose -f test_server.yaml up server --exit-code-from server
```

Or locally with a running PostgreSQL instance and `.test_env`:
```bash
cd server
pytest -vvv
```

**Frontend:**
```bash
cd client
npm test           # watch mode
npm run test:ci    # CI mode
```

## Starting the Project

**Full stack via Docker Compose:**
```bash
docker compose -f test_server.yaml up      # test environment
docker compose -f build_data.yml up        # with wikidata/wiki_link services
```

**Backend only:**
```bash
cd server
pip install -r requirements.txt
# Set required env vars (see below)
uvicorn the_history_atlas.main:app --reload
```

**Frontend only:**
```bash
cd client
npm install
npm start    # http://localhost:3000
```

## Required Environment Variables

| Variable | Purpose |
|----------|---------|
| `THA_DB_URI` | PostgreSQL connection string |
| `SEC_KEY` | Base64-encoded Fernet encryption key |
| `REFRESH_BY` | Token refresh interval (seconds) |
| `TTL` | Token time-to-live (seconds) |
| `ADMIN_USERNAME` | Admin login (default: `admin`) |
| `ADMIN_PASSWORD` | Admin password (default: `admin`) |
| `POSTGRES_PASS` | DB password for Docker Compose |

Local dev uses `.env.local`; tests use `.test_env`.

## Code Quality

**Backend:** Black for formatting.
```bash
cd server && black .
```

**Frontend:** Prettier + ESLint (via Create React App).
```bash
cd client && npx prettier --write src/
```

## Database Migrations

Migrations live in `/server/alembic/versions/` and are managed with Alembic. They run automatically in the Docker test pipeline.

```bash
cd server
alembic upgrade head     # apply migrations
alembic revision --autogenerate -m "description"  # create new migration
```

## CI/CD

GitHub Actions workflows in `.github/workflows/`:
- `test-server.yml` — Backend tests on PRs to `dev`
- `test-client.yml` — Frontend tests on `dev` pushes/PRs
- `test-wiki-link.yml` / `test-wikidata.yml` — Service tests
- `build-server-image.yml` — Builds multi-arch Docker images (amd64 + arm64) and pushes to Docker Hub

## Key Patterns

- **API handlers** live in `server/the_history_atlas/api/handlers/` — one file per domain area (history, tags, users)
- **Pydantic models** for request/response types live in `server/the_history_atlas/api/types/`
- **Domain logic** lives in `server/the_history_atlas/apps/`
- **React pages** are in `client/src/pages/`, reusable components in `client/src/components/`
- Prometheus metrics are exposed via `prometheus-fastapi-instrumentator`
