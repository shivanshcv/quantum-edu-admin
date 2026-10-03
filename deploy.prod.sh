#!/bin/bash
#
# Redeploy only the Django admin to the Oracle Cloud VM.
# The admin is the `admin` service of the stack in quantum-edu-be/deploy/oracle; this delegates to
# quantum-edu-be/deploy.prod.sh, which syncs this repo, uploads config and rebuilds the container.
#
#   ./deploy.prod.sh            # rebuild + restart admin
#   ./deploy.prod.sh --status   # container status and logs
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BE_DIR="${BE_DIR:-$SCRIPT_DIR/../quantum-edu-be}"

if [[ ! -x "$BE_DIR/deploy.prod.sh" ]]; then
  echo "quantum-edu-be not found at $BE_DIR (set BE_DIR=/path/to/quantum-edu-be)" >&2
  exit 1
fi

export ADMIN_DIR="$SCRIPT_DIR"
export DEPLOY_PROD_ENV_FILE="${DEPLOY_PROD_ENV_FILE:-$BE_DIR/deploy.prod.env}"

if [[ "$1" == "--status" ]]; then
  exec "$BE_DIR/deploy.prod.sh" --status
fi
exec "$BE_DIR/deploy.prod.sh" --only admin "$@"
