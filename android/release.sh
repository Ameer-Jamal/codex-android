#!/usr/bin/env bash
# Small control requests only: builds and package transfers stay on GitHub.
set -euo pipefail
repo=Ameer-Jamal/codex-android
usage() {
  cat <<'HELP'
Usage: bash android/release.sh COMMAND [ARGS]
  status                           Show recent CI, staging, mirrors and npm latest
  build                            Start an Android build on main
  watch RUN_ID                     Wait for a GitHub run (no AI needed)
  inspect STAGING_RUN_ID            Show package checksum and npm stage ID
  stage BUILD_RUN_ID               Stage an exact, successful main build on GitHub
  login                            Sign into npm using its official browser flow
  approve STAGE_ID                  Inspect and approve an already uploaded stage
  mirror VERSION SHA256 COMMIT NOTES_FILE
                                   Create a prerelease if needed, then mirror on GitHub
No command uploads or downloads a full package on this computer.
HELP
}
fail() { printf '%s\n' "$*" >&2; exit 2; }
run_id() { [[ "$1" =~ ^[0-9]+$ ]] || fail 'Run ID must contain digits only'; }
command=${1:-status}
if [[ $# -gt 0 ]]; then shift; fi
case "$command" in
  status)
    [[ $# -eq 0 ]] || fail 'status takes no arguments'
    for workflow in android.yml android-publish.yml android-release-assets.yml; do
      gh run list --repo "$repo" --workflow "$workflow" --limit 3
    done
    npm view codex-android dist-tags --json
    ;;
  build)
    [[ $# -eq 0 ]] || fail 'build takes no arguments'
    gh workflow run android.yml --repo "$repo" --ref main
    ;;
  watch)
    [[ $# -eq 1 ]] || fail 'watch requires RUN_ID'
    run_id "$1"
    gh run watch "$1" --repo "$repo" --interval 30 --exit-status
    ;;
  inspect)
    [[ $# -eq 1 ]] || fail 'inspect requires STAGING_RUN_ID'
    run_id "$1"
    gh run view "$1" --repo "$repo" --log |
      awk '/Package: codex-android@|npm notice shasum:|staged with id/'
    ;;
  stage)
    [[ $# -eq 1 ]] || fail 'stage requires BUILD_RUN_ID'
    run_id "$1"
    # The workflow itself verifies repository, source commit and build success.
    gh workflow run android-publish.yml --repo "$repo" --ref main -f "build_run_id=$1"
    ;;
  login)
    [[ $# -eq 0 ]] || fail 'login takes no arguments'
    npx --yes npm@11.21.0 login --auth-type=web --registry=https://registry.npmjs.org/
    ;;
  approve)
    [[ $# -eq 1 ]] || fail 'approve requires STAGE_ID'
    [[ "$1" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]] || fail 'Invalid stage ID'
    npx --yes npm@11.21.0 stage view "$1" --json
    printf '\nReview the package version, checksum and tag above before approving in your browser.\n'
    npx --yes npm@11.21.0 stage approve "$1" --auth-type=web
    ;;
  mirror)
    [[ $# -eq 4 ]] || fail 'mirror requires VERSION SHA256 COMMIT NOTES_FILE'
    [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+-android\.[0-9]+$ ]] || fail 'Invalid Android version'
    [[ "$2" =~ ^[0-9a-f]{64}$ ]] || fail 'Invalid SHA-256'
    [[ "$3" =~ ^[0-9a-f]{40}$ ]] || fail 'Use the complete source commit SHA'
    [[ -f "$4" ]] || fail 'Release notes file does not exist'
    if ! gh release view "v$1" --repo "$repo" >/dev/null; then
      gh release create "v$1" --repo "$repo" --target "$3" --prerelease \
        --title "Codex for Android $1" --notes-file "$4"
    fi
    gh workflow run android-release-assets.yml --repo "$repo" --ref main \
      -f "version=$1" -f "sha256=$2"
    ;;
  help|--help|-h) usage ;;
  *) usage >&2; fail "Unknown command: $command" ;;
esac
