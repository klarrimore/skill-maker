#!/usr/bin/env bash
# Smoke-drive every runnable surface of skill-maker. Run from the repo root:
#   bash scripts/smoke.sh
# Exits non-zero on the first failed check.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
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

# 2b. The fixture still carries the violations it is meant to test (guards against
#     an eval run "fixing" it in place and silently disarming the negative case)
python3 - "$SKILL_DIR/evals/files/broken-skill/SKILL.md" <<'EOF' >/dev/null 2>&1
import sys
text = open(sys.argv[1], encoding="utf-8").read()
required = ["name: Weekly_Log_Summary", "<error logs>", "author:", "version:"]
sys.exit(0 if all(token in text for token in required) else 1)
EOF
check "fixture: broken-skill still carries its violations" 0 $?

# 2c. The valid fixture passes (input for the improve-installed-skill eval)
python3 -m scripts.quick_validate evals/files/standup-summary >/dev/null 2>&1
check "validate: standup-summary fixture is valid" 0 $?

# 3. Unit tests (stdlib unittest, no third-party deps)
python3 -m unittest discover -s tests -t . >/dev/null 2>&1
check "unittest: tests/ suite passes" 0 $?

# 3b. Grader agrees with the validator: passes on the skill, fails on the fixture
python3 -m evals.grade_artifacts . >/dev/null 2>&1
check "grade: artifacts checker passes on skill-maker" 0 $?
python3 -m evals.grade_artifacts evals/files/broken-skill >/dev/null 2>&1
check "grade: artifacts checker rejects broken fixture" 1 $?

# 4. Direct invocation: the internal functions import and run without the CLI
python3 - <<'EOF' >/dev/null 2>&1
from pathlib import Path
from scripts.utils import parse_frontmatter
from scripts.quick_validate import validate_skill, body_warnings
from scripts.package_skill import should_exclude
fm, body = parse_frontmatter(Path("SKILL.md").read_text())
assert fm["name"] == "skill-maker" and body
assert validate_skill(".") == (True, "Skill is valid!")
assert isinstance(body_warnings("."), list)
assert should_exclude(Path("x/tests/t.py")) and not should_exclude(Path("x/SKILL.md"))
EOF
check "direct: internals import and run" 0 $?

# 5. Packaging produces a .skill zip with no dev artifacts inside
python3 -m scripts.package_skill . "$DIST" >/dev/null 2>&1
check "package: .skill produced" 0 $?
python3 - "$DIST/skill-maker.skill" <<'EOF'
import sys, zipfile
names = zipfile.ZipFile(sys.argv[1]).namelist()
bad = [n for n in names if any(x in n for x in ("tests/", "evals/", "__pycache__", ".pytest_cache"))]
sys.exit(1 if bad else 0)
EOF
check "package: zip excludes tests/evals/caches" 0 $?

# 5b. Installer builds a clean copy and installs it into a target directory
INSTALL_TARGET="$(mktemp -d)"
python3 -m scripts.install_skill evals/files/standup-summary --target "$INSTALL_TARGET" >/dev/null 2>&1
check "install: valid skill installs" 0 $?
test -f "$INSTALL_TARGET/standup-summary/SKILL.md"
check "install: SKILL.md at destination" 0 $?
python3 - "$INSTALL_TARGET" <<'EOF'
import sys
from pathlib import Path
bad = [p for p in Path(sys.argv[1]).rglob('*')
       if any(x in p.parts for x in ('tests', 'evals', '__pycache__', '.pytest_cache'))]
sys.exit(1 if bad else 0)
EOF
check "install: no dev artifacts installed" 0 $?
python3 -m scripts.install_skill evals/files/standup-summary --target "$INSTALL_TARGET" >/dev/null 2>&1
check "install: rerun without --force exits 2" 2 $?
python3 -m scripts.install_skill evals/files/standup-summary --target "$INSTALL_TARGET" --force >/dev/null 2>&1
check "install: --force replaces" 0 $?
python3 -m scripts.install_skill evals/files/broken-skill --target "$INSTALL_TARGET" >/dev/null 2>&1
check "install: invalid skill refused" 1 $?
INSTALL_DRYRUN="$(mktemp -d)"; rmdir "$INSTALL_DRYRUN"
python3 -m scripts.install_skill evals/files/standup-summary --target "$INSTALL_DRYRUN" --dry-run >/dev/null 2>&1
check "install: dry-run exits 0" 0 $?
test ! -e "$INSTALL_DRYRUN"
check "install: dry-run writes nothing" 0 $?
rm -rf "$INSTALL_TARGET" "$INSTALL_DRYRUN"

# 6. Generic evaluator: offline audit, paired run, benchmark, and sandboxed improve
GENERIC_WORKSPACE="$(mktemp -d)"
python3 -m scripts.skill_eval audit evals/files/eval-suite-valid --workspace "$GENERIC_WORKSPACE/audit" >/dev/null 2>&1
check "eval: offline audit passes" 0 $?
python3 -m scripts.skill_eval run evals/files/eval-suite-valid --workspace "$GENERIC_WORKSPACE/run" \
  --runs 1 --adapter-arg python3 --adapter-arg tests/fixtures/fake_eval_adapter.py >/dev/null 2>&1
check "eval: paired run records baseline failures" 1 $?
test -f "$GENERIC_WORKSPACE/run/runs/1-with_skill-1/grading.json"
check "eval: with-skill grading record exists" 0 $?
test -f "$GENERIC_WORKSPACE/run/runs/1-without_skill-1/grading.json"
check "eval: baseline grading record exists" 0 $?
python3 -m scripts.skill_eval benchmark evals/files/eval-suite-valid --workspace "$GENERIC_WORKSPACE/run" >/dev/null 2>&1
check "eval: benchmark produced" 0 $?
python3 -m scripts.skill_eval improve evals/files/eval-suite-valid --workspace "$GENERIC_WORKSPACE/improve" \
  --max-iterations 2 --runs 1 --adapter-arg python3 --adapter-arg tests/fixtures/fake_eval_adapter.py >/dev/null 2>&1
check "eval: held-out candidate promoted" 0 $?
python3 - "$GENERIC_WORKSPACE/improve" <<'EOF' >/dev/null 2>&1
import sys
from pathlib import Path
from scripts.quick_validate import validate_skill
root = Path(sys.argv[1])
best = root / "best-skill" / "eval-suite-valid"
valid, message = validate_skill(best)
assert valid, message
assert (root / "history.json").exists()
EOF
check "eval: promoted copy revalidates" 0 $?
python3 - "$SKILL_DIR/evals/files/eval-suite-valid" "$GENERIC_WORKSPACE/improve" <<'EOF' >/dev/null 2>&1
import hashlib
import sys
from pathlib import Path
def digest(root):
    values = []
    for path in sorted(Path(root).rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            values.append((str(path.relative_to(root)), hashlib.sha256(path.read_bytes()).hexdigest()))
    return values
assert digest(sys.argv[1]) == digest(Path(sys.argv[2]) / "candidates" / "v0" / "eval-suite-valid")
EOF
check "eval: source fixture remains byte-identical" 0 $?
rm -rf "$GENERIC_WORKSPACE"

# 6b. Shipped evaluator scripts survive packaging and installation, while dev trees do not
python3 - "$DIST/skill-maker.skill" <<'EOF'
import sys, zipfile
names = set(zipfile.ZipFile(sys.argv[1]).namelist())
required = {"scripts/eval_models.py", "scripts/eval_adapter.py", "scripts/eval_store.py", "scripts/skill_eval.py"}
assert required <= names
assert not any(name.startswith("tests/") or name.startswith("evals/") for name in names)
EOF
check "package: evaluator scripts included" 0 $?
INSTALL_SKILL_MAKER="$(mktemp -d)"
python3 -m scripts.install_skill . --target "$INSTALL_SKILL_MAKER" >/dev/null 2>&1
check "install: skill-maker with evaluator scripts" 0 $?
test -f "$INSTALL_SKILL_MAKER/skill-maker/scripts/skill_eval.py"
check "install: evaluator CLI at destination" 0 $?
python3 - "$INSTALL_SKILL_MAKER/skill-maker" <<'EOF' >/dev/null 2>&1
import sys
from pathlib import Path
bad = [path for path in Path(sys.argv[1]).rglob("*") if any(part in ("tests", "evals") for part in path.parts)]
assert not bad, bad
EOF
check "install: target dev trees excluded" 0 $?
rm -rf "$INSTALL_SKILL_MAKER"

# 7. Eval-review UI renders from real data (all placeholders filled)
cd "$REPO_ROOT"
python3 scripts/render_review.py "$SKILL_DIR" /tmp/eval_review_rendered.html >/dev/null 2>&1
check "render: eval_review.html filled from real data" 0 $?

# 8. Screenshot the rendered UI (skipped when no chrome)
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
