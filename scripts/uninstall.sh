#!/usr/bin/env bash
# uninstall.sh — Remove Hermes Windows Skills
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
SKILLS_DIR="${HERMES_HOME}/skills"

echo "Hermes Windows Skills — Uninstall"
echo "=================================="

removed=0; not_found=0

for skill_dir in "$REPO_DIR/skills/"*/*/; do
    name="$(basename "$skill_dir")"
    target="$SKILLS_DIR/$name"
    # Skip files, only directories with SKILL.md
    [[ ! -d "$skill_dir" ]] && continue
    [[ ! -f "${skill_dir}SKILL.md" ]] && continue
    if [[ -d "$target" ]]; then
        rm -rf "$target"
        echo "  Removed: $name"
        removed=$((removed+1))
    else
        echo "  Not installed: $name"
        not_found=$((not_found+1))
    fi
done

echo ""
echo "Done. $removed removed, $not_found not found."
