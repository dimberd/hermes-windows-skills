#!/usr/bin/env bash
# install.sh — Hermes Windows Skills Installer
# Usage: bash scripts/install.sh [--dry-run] [--profile NAME]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
SKILLS_DIR="${HERMES_HOME}/skills"
DRY_RUN=false
PROFILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true; shift ;;
        --profile) PROFILE="$2"; shift 2 ;;
        --help) echo "Usage: $0 [--dry-run] [--profile NAME]"; exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

[[ -n "$PROFILE" ]] && SKILLS_DIR="${HERMES_HOME}/profiles/${PROFILE}/skills"

echo "Hermes Windows Skills Installer"
echo "================================"
echo "Source:      $REPO_DIR/skills/"
echo "Target:      $SKILLS_DIR"
[[ "$DRY_RUN" == true ]] && echo "Mode:        DRY RUN"
echo ""

if ! command -v hermes &>/dev/null; then
    echo "  Warning: 'hermes' not found in PATH."
fi

[[ "$DRY_RUN" == false ]] && mkdir -p "$SKILLS_DIR"

installed=0
for skill_dir in "$REPO_DIR/skills/"*/*/; do
    skill_name="$(basename "$skill_dir")"
    target_path="$SKILLS_DIR/$skill_name"
    # Skip non-skill directories
    [[ ! -d "$skill_dir" ]] && continue
    [[ ! -f "${skill_dir}SKILL.md" ]] && continue

    if [[ -d "$target_path" ]]; then
        echo "  Updating: $skill_name"
    else
        echo "  Installing: $skill_name"
    fi

    [[ "$DRY_RUN" == false ]] && cp -r "$skill_dir" "$target_path"
    installed=$((installed + 1))
done

echo ""
echo "Done. $installed skill(s) installed."
echo "Start a new Hermes session and use: /skill <name>"
