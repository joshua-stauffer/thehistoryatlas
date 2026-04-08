---
name: test-server
description: Run the server test suite using .test_env variables and the project virtualenv
allowed-tools: Bash(docker:*), Bash(cd:*), Read, Grep
---

# Run Server Tests

Run the backend test suite for the History Atlas server.

## Usage

`/test-server [args]`

Arguments are passed to pytest. Examples:

- `/test-server` — run the full suite
- `/test-server -k test_nearby` — run tests matching a pattern
- `/test-server tests/test_history.py` — run a specific test file
- `/test-server -x` — stop on first failure

## Execution

Run via Docker Compose (the standard method from CLAUDE.md):

```bash
cd /Users/josh/dev/thehistoryatlas
docker compose -f test_server.yaml up server --exit-code-from server
```

If arguments are provided, run locally with the test environment instead:

```bash
cd /Users/josh/dev/thehistoryatlas/server
set -a && source /Users/josh/dev/thehistoryatlas/.test_env && set +a
/Users/josh/dev/thehistoryatlas/env/bin/python -m pytest -vvv $ARGUMENTS
```

## Important

- **ALWAYS** use `.test_env` for environment variables — NEVER `.env.local` (that points at production).
- **ALWAYS** use the project virtualenv at `/Users/josh/dev/thehistoryatlas/env`.
- Tests require a running PostgreSQL instance when running locally (Docker handles this automatically).
