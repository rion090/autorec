#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# lint.sh — Lint all Python source files in AutoRec
#
# Usage:
#   bash scripts/lint.sh          # lint all files in src/
#   bash scripts/lint.sh strict   # also run flake8 style checks
#
# Requires: python3 (always), flake8 (optional for strict mode)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
CYAN="\033[96m"
BOLD="\033[1m"
RESET="\033[0m"

ok()   { echo -e "${GREEN}[✔]${RESET} $*"; }
warn() { echo -e "${YELLOW}[!]${RESET} $*"; }
err()  { echo -e "${RED}[✘]${RESET} $*"; }
info() { echo -e "${CYAN}[→]${RESET} $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$REPO_ROOT/src"

STRICT=${1:-""}
PASS=0
FAIL=0

echo -e "\n${BOLD}${CYAN}AutoRec — Python Linter${RESET}\n"

# ── Step 1: syntax check (always) ────────────────────────────────────────────
info "Running syntax check (python3 -m py_compile) …\n"

while IFS= read -r -d '' pyfile; do
    rel="${pyfile#$REPO_ROOT/}"
    if python3 -m py_compile "$pyfile" 2>/tmp/lint_err; then
        ok "$rel"
        PASS=$((PASS + 1))
    else
        err "$rel"
        cat /tmp/lint_err
        FAIL=$((FAIL + 1))
    fi
done < <(find "$SRC_DIR" -name "*.py" -print0)

echo

# ── Step 2: flake8 style check (strict mode only) ────────────────────────────
if [[ "$STRICT" == "strict" ]]; then
    if ! command -v flake8 &>/dev/null; then
        warn "flake8 not installed — skipping style check."
        warn "Install with:  pip install flake8"
    else
        info "Running style check (flake8, max-line-length=100) …\n"
        if flake8 "$SRC_DIR" \
               --max-line-length=100 \
               --ignore=E501,W503 \
               --statistics; then
            ok "No style issues found."
        else
            warn "Style issues found above (non-blocking in normal mode)."
        fi
    fi
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo -e "\n${BOLD}─────────────────────────────────────────${RESET}"
echo -e "  Passed : ${GREEN}${PASS}${RESET}"
echo -e "  Failed : ${RED}${FAIL}${RESET}"
echo -e "${BOLD}─────────────────────────────────────────${RESET}\n"

[[ $FAIL -eq 0 ]]
