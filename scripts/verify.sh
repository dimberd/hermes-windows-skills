#!/usr/bin/env bash
# verify.sh — Validate SKILL.md files against Hermes Agent standards
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SKILLS_DIR="${REPO_DIR}/skills"
EXIT_CODE=0

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo "Hermes Windows Skills — Validation"
echo "===================================="

[[ ! -d "$SKILLS_DIR" ]] && { echo "Skills directory not found"; exit 1; }

PYTHON_CMD=""
command -v python3 &>/dev/null && PYTHON_CMD="python3"
[[ -z "$PYTHON_CMD" ]] && command -v python &>/dev/null && PYTHON_CMD="python"

found=0; passed=0; failed=0

for skill_file in $(find "$SKILLS_DIR" -name "SKILL.md" -type f | sort); do
    skill_dir="$(dirname "$skill_file")"
    name="$(basename "$skill_dir")"
    file="$skill_file"
    found=$((found + 1)); errs=0

    echo -e "${YELLOW}${name}${NC}"

    [[ ! -f "$file" ]] && { echo -e "  ${RED}SKILL.md not found${NC}"; failed=$((failed+1)); continue; }

    head -c3 "$file" | grep -c -- "---" >/dev/null 2>&1 || { echo -e "  ${RED}Must start with ---${NC}"; errs=$((errs+1)); }

    sz=$(wc -c < "$file")
    [[ "$sz" -gt 100000 ]] && { echo -e "  ${RED}File too large: ${sz}${NC}"; errs=$((errs+1)); }

    [[ "${#name}" -gt 64 ]] && { echo -e "  ${RED}Name > 64 chars${NC}"; errs=$((errs+1)); }

    [[ "$name" =~ ^[a-z0-9][a-z0-9-]*$ ]] || { echo -e "  ${RED}Invalid name format${NC}"; errs=$((errs+1)); }

    if [[ -n "$PYTHON_CMD" ]]; then
        result=$($PYTHON_CMD -c "
import re, sys
c = open('$file').read()
if not c.startswith('---'): print('FAIL: starts'); sys.exit(1)
r = c[3:]; m = re.search(r'\n---\s*\n', r)
if not m: print('FAIL: no close'); sys.exit(1)
try:
    import yaml; fm = yaml.safe_load(r[:m.start()])
except:
    fm = {}
    for l in r[:m.start()].split('\n'):
        if ':' in l: k,v=l.split(':',1); fm[k.strip()]=v.strip()
if not fm: print('FAIL: empty fm'); sys.exit(1)
for f in ['name','description']:
    if f not in fm: print(f'FAIL: missing {f}'); sys.exit(1)
d = fm['description']
if len(d) > 1024: print(f'FAIL: desc {len(d)}/1024'); sys.exit(1)
print('PASS')
" 2>&1) || true
        [[ "$result" == *FAIL* ]] && { echo -e "  ${RED}${result}${NC}"; errs=$((errs+1)); }
    fi

    [[ "$errs" -eq 0 ]] && { echo -e "  ${GREEN}PASS${NC}"; passed=$((passed+1)); } || { echo -e "  ${RED}FAIL (${errs})${NC}"; failed=$((failed+1)); EXIT_CODE=1; }
done

echo "===================================="
echo -e "${GREEN}$passed passed${NC}, ${RED}$failed failed${NC}, $found total"
exit $EXIT_CODE
