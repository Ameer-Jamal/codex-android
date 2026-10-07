#!/usr/bin/env bash
# Run on the actual device after installing a built Android artifact.
set -euo pipefail
codex_cmd="${CODEX_CMD:-codex}"
"$codex_cmd" --version
"$codex_cmd" --help >/dev/null
"$codex_cmd" exec --help >/dev/null
"$codex_cmd" login status
if [[ "${1:-}" == --live ]]; then
  # Requires authentication. Keep the configured approval and sandbox policy.
  "$codex_cmd" exec 'Reply with exactly: Android runtime OK'
elif [[ $# -gt 0 ]]; then
  echo "Usage: $0 [--live] (CODEX_CMD may select an installed binary)" >&2
  exit 2
fi
