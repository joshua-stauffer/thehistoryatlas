---
description: Run the server test suite using .test_env variables and the project virtualenv
allowed-tools: Bash
---

Run the server tests with the correct environment and virtualenv. Use `.test_env` for all environment variables — never `.env.local`.

```bash
cd /Users/josh/dev/thehistoryatlas/server && source /Users/josh/dev/thehistoryatlas/env/bin/activate && set -a && source ../.test_env && set +a && python -m pytest $ARGUMENTS -v 2>&1
```

If `$ARGUMENTS` was not provided, run the full suite: `python -m pytest -v`.

Report a summary of passed/failed tests and any error output.
