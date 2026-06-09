#!/usr/bin/env bash
# chora-hook.sh — DevWater post-session hook for Chora
#
# Usage:
#   chora-hook.sh [SESSION_DIR]
#
# DevWater can call this on SessionEnd or PreCompact events:
#   hooks:
#     SessionEnd: ~/.kimi/skills/chora/scripts/chora-hook.sh
#
# The script forwards the session directory to Chora via the
# CHORA_SESSION_DIR environment variable and runs in silent hook mode.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHORA_PY="${SCRIPT_DIR}/chora.py"

export CHORA_SESSION_DIR="${1:-${DEVWATER_SESSION_DIR:-}}"

if [[ -z "${CHORA_SESSION_DIR}" ]]; then
    echo "chora-hook: no session directory provided." >&2
    echo "  Pass it as an argument or set DEVWATER_SESSION_DIR." >&2
    exit 1
fi

if [[ ! -d "${CHORA_SESSION_DIR}" ]]; then
    echo "chora-hook: session directory not found: ${CHORA_SESSION_DIR}" >&2
    exit 1
fi

exec python3 "${CHORA_PY}" --hook
