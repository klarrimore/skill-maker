#!/usr/bin/env bash
# Smoke-drive every runnable surface of skill-maker. Run from the repo root:
#   bash .claude/skills/run-skill-maker/smoke.sh
# Exits non-zero on the first failed check.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SKILL_DIR="$REPO_ROOT/skills/skill-maker"
DIST="$(mktemp -d)"
FAIL=0

check() { # check <label> <expected_exit> <actual_exit>
  if [ "$2" -eq "$3" ]; then echo "ok   $1"; else echo "FAIL $1 (expected exit $2, got $3)"; FAIL=1; fi
}

cd "$SKILL_DIR"

# 1. Validator passes on the skill itself
python3 -m scripts.quick_validate . >/dev/null 2>&1
check "validate: skill-maker is spec-valid" 0 $?

# 2. Validator fails on the deliberately broken fixture
python3 -m scripts.quick_validate evals/files/broken-skill >/dev/null 2>&1
check "validate: broken fixture rejected" 1 $?

# 3. Unit tests
python3 -m pytest tests/ -q >/dev/null 2>&1
check "pytest: tests/ suite passes" 0 $?

# 4. Packaging produces a .skill zip with no dev artifacts inside
python3 -m scripts.package_skill . "$DIST" >/dev/null 2>&1
check "package: .skill produced" 0 $?
python3 - "$DIST/skill-maker.skill" <<'EOF'
import sys, zipfile
names = zipfile.ZipFile(sys.argv[1]).namelist()
bad = [n for n in names if any(x in n for x in ("tests/", "evals/", "__pycache__", ".pytest_cache"))]
sys.exit(1 if bad else 0)
EOF
check "package: zip excludes tests/evals/caches" 0 $?

# 5. Eval-review UI renders from real data (all placeholders filled)
cd "$REPO_ROOT"
python3 .claude/skills/run-skill-maker/render_review.py "$SKILL_DIR" /tmp/eval_review_rendered.html >/dev/null 2>&1
check "render: eval_review.html filled from real data" 0 $?

# 6. Screenshot the rendered UI (skipped when no chrome)
if command -v google-chrome >/dev/null; then
  timeout 60 google-chrome --headless --disable-gpu --window-size=1200,1600 \
    --screenshot=/tmp/eval_review_screenshot.png file:///tmp/eval_review_rendered.html >/dev/null 2>&1
  check "screenshot: /tmp/eval_review_screenshot.png" 0 $?
else
  echo "skip screenshot (no google-chrome)"
fi

rm -rf "$DIST"
find "$SKILL_DIR" -name '__pycache__' -o -name '.pytest_cache' | xargs rm -rf 2>/dev/null

[ "$FAIL" -eq 0 ] && echo "ALL OK" || echo "FAILURES ABOVE"
exit "$FAIL"
