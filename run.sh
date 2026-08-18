#!/usr/bin/env bash
# Start Willa. Runs ./setup.sh --check first, so a missing dependency is
# reported as a list of steps rather than as a traceback.

set -euo pipefail
cd "$(dirname "$0")"

./setup.sh --check || {
  printf '\nRun \033[1m./setup.sh\033[0m first.\n'
  exit 1
}

# shellcheck disable=SC1091
source .venv/bin/activate

printf '\n\033[1mWilla\033[0m  http://127.0.0.1:8000   (ctrl-c to stop)\n'
printf 'Bound to loopback. Nothing you type leaves this machine.\n\n'

exec uvicorn app.main:app --host 127.0.0.1 --port 8000 "$@"
