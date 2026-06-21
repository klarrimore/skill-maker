# Project Architecture Blueprint

> Generated: 2026-06-21 (refreshed)  
> Repository: `klarrimore/skill-maker`  
> Version: 1.1 (per `SKILL.md` frontmatter `metadata.version`)  
> Latest commit: `c6beb74`

---

## 1. Architectural Overview

**skill-maker** is a meta-skill — an Agent Skill that creates, validates, evaluates, and packages other Agent Skills conforming to the open [agentskills.io](https://agentskills.io) standard. It is not a traditional application but a **content-as-architecture** system: structured Markdown files drive agent behavior, Python scripts handle deterministic operations, and a well-defined directory convention enforces progressive disclosure of context.

### Guiding Principles

| Principle | How Enforced |
|-----------|-------------|
| **Portability** | Core spec uses only 6 frontmatter fields; no client-specific extensions in the primary artifact |
| **Progressive disclosure** | Three-tier loading: metadata (always), body (on activation), references (on demand) |
| **Convention over configuration** | Directory name must match `name` field; layout is fixed by spec |
| **Lean entry point** | `SKILL.md` stays under 500 lines / ~5000 tokens; depth lives in `references/` |
| **Zero-network fallback** | Validation and packaging work offline via bundled Python scripts |

### Architecture Pattern

**Document-Driven Agent Architecture** — a pattern where:
- Structured Markdown documents are the primary "source code" that agents execute
- Python scripts provide deterministic validation and packaging
- Directory conventions form the component boundaries
- The spec standard (agentskills.io) serves as the architectural contract

---

## 2. Architecture Visualization (C4 Style)

### Level 1: System Context

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Runtime                         │
│  (Claude Code, Copilot CLI, or any skills-compatible)   │
└───────────────────────────┬─────────────────────────────┘
                            │ loads
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     skill-maker/                         │
│  ┌──────────┐  ┌────────────┐  ┌─────────┐  ┌───────┐ │
│  │ SKILL.md │→ │references/ │  │scripts/ │  │assets/│ │
│  │(entry pt)│  │(on-demand) │  │(tools)  │  │(tmpl) │ │
│  └──────────┘  └────────────┘  └─────────┘  └───────┘ │
└─────────────────────────────────────────────────────────┘
                            │ produces
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Output Skill Folder                         │
│  skill-name/SKILL.md + scripts/ + references/ + assets/ │
└─────────────────────────────────────────────────────────┘
```

### Level 2: Component Interaction

```
┌─────────────────── skill-maker/ ───────────────────────────┐
│                                                             │
│  SKILL.md (240 lines)                                      │
│  ├── Frontmatter (metadata: name, description, license,    │
│  │    compatibility, metadata)                              │
│  └── Body (the core loop: capture → draft → test →         │
│       evaluate → optimize → validate → distribute)         │
│       │                                                     │
│       │ points to (on demand)                               │
│       ▼                                                     │
│  references/                                                │
│  ├── spec-reference.md  ←── "Read before writing FM"       │
│  ├── authoring-guide.md ←── "Read before writing body"     │
│  ├── evaluation.md      ←── "Full eval workflow"           │
│  ├── description-optimization.md ←── "Trigger tuning"      │
│  ├── environment-adaptations.md  ←── "Runtime constraints" │
│  └── schemas.md         ←── "JSON structures"              │
│                                                             │
│  scripts/ (Python 3.8+, PyYAML)                            │
│  ├── quick_validate.py  ←── validate_skill() → (bool,msg) │
│  ├── package_skill.py   ←── package_skill() → .skill zip  │
│  └── utils.py           ←── parse_skill_md() → tuple      │
│                                                             │
│  assets/                                                    │
│  └── eval_review.html   ←── Interactive eval review UI     │
│                                                             │
│  .agents/                                                   │
│  ├── instructions/      ←── Canonical reusable docs        │
│  │   ├── agent-safety.instructions.md                      │
│  │   ├── markdown-gfm.instructions.md                      │
│  │   └── update-docs-on-code-change.instructions.md        │
│  └── skills/            ←── Build-tooling skills (dev only)│
│                                                             │
│  .github/instructions/  ←── Platform forwarders            │
│                                                             │
│  AGENTS.md              ←── Repo-wide agent guidance       │
│  CLAUDE.md              ←── Claude Code bootstrap          │
│  .github/copilot-instructions.md ←── Copilot bootstrap    │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow: Skill Creation Pipeline

```
User Request
    │
    ▼
[1. Capture Intent] ─── conversation mining, 4-point checklist
    │
    ▼
[2. Interview & Research] ─── edge cases, formats, dependencies
    │
    ▼
[3. Draft SKILL.md] ─── reads: spec-reference.md, authoring-guide.md
    │
    ▼
[4. Test Cases] ─── writes: evals/evals.json (schema: schemas.md)
    │
    ▼
[5. Evaluate & Improve] ─── reads: evaluation.md
    │                         spawns: with-skill + baseline runs
    │                         outputs: workspace/iteration-N/
    │
    ▼
[6. Optimize Description] ─── reads: description-optimization.md
    │                          uses: assets/eval_review.html
    │
    ▼
[7. Validate] ─── runs: scripts/quick_validate.py
    │               or: skills-ref validate
    │
    ▼
[8. Package & Distribute] ─── runs: scripts/package_skill.py
                               outputs: <name>.skill (zip)
```

---

## 3. Core Architectural Components

### 3.1 SKILL.md — The Entry Point

| Aspect | Detail |
|--------|--------|
| **Purpose** | Single source of truth for the skill's behavior; the agent reads and follows it |
| **Internal structure** | YAML frontmatter (6 fields max) + Markdown body (imperative instructions) |
| **Budget** | ≤500 lines, ~5000 tokens |
| **Interaction** | Loaded by agent runtimes on description-match; points to references on demand |
| **Extension** | Add depth via `references/`, automation via `scripts/` |

### 3.2 references/ — Progressive Disclosure Layer

| File | When Loaded | Purpose |
|------|-------------|---------|
| `spec-reference.md` | Before writing frontmatter | Exact schema, naming rules, portability |
| `authoring-guide.md` | Before writing body | Writing patterns, do's and don'ts |
| `evaluation.md` | During test & improve phase | Full eval workflow with subagents |
| `description-optimization.md` | After skill works | Trigger tuning method |
| `environment-adaptations.md` | When capabilities are missing | Graceful degradation |
| `schemas.md` | When writing JSON artifacts | Structure definitions for evals/grading |

### 3.3 scripts/ — Deterministic Operations

A Python package (3 modules) providing validation and packaging:

```python
# Public API
validate_skill(skill_path) -> (bool, message)  # quick_validate.py
body_warnings(skill_path) -> list[str]          # quick_validate.py
package_skill(skill_path, output_dir) -> Path   # package_skill.py
parse_skill_md(skill_path) -> (name, desc, content)  # utils.py
```

**Dependency chain:** `package_skill.py` imports `validate_skill` from `quick_validate.py`. Both are standalone — no external dependencies beyond Python 3.8+ and PyYAML.

### 3.4 assets/ — Output Templates

`eval_review.html` is an interactive single-file web app (vanilla JS, no build step) for reviewing and editing eval sets. It uses placeholder tokens (`__SKILL_NAME_PLACEHOLDER__`, `__EVAL_DATA_PLACEHOLDER__`) filled at runtime.

### 3.5 .agents/instructions/ — Cross-Cutting Governance

Canonical instruction documents that apply across the repository and any agent working within it. Platform-specific forwarders in `.github/instructions/` point here for auto-discovery.

---

## 4. Architectural Layers and Dependencies

```
┌────────────────────────────────────────────────────────┐
│  Layer 1: Agent Bootstrap                              │
│  AGENTS.md, CLAUDE.md, .github/copilot-instructions.md │
│  Purpose: Platform-specific entry; points to AGENTS.md │
└────────────────────────┬───────────────────────────────┘
                         │ references
                         ▼
┌────────────────────────────────────────────────────────┐
│  Layer 2: Skill Instructions (SKILL.md)               │
│  Purpose: The behavioral contract; the "application"   │
└────────────────────────┬───────────────────────────────┘
                         │ loads on demand
                         ▼
┌────────────────────────────────────────────────────────┐
│  Layer 3: Reference Documentation (references/)        │
│  Purpose: Deep knowledge; loaded only when needed      │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  Layer 4: Executable Scripts (scripts/)                │
│  Purpose: Deterministic validation & packaging         │
│  Dependency: PyYAML (external), utils.py (internal)    │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  Layer 5: Governance (.agents/instructions/)           │
│  Purpose: Cross-cutting safety, style, doc-update rules│
└────────────────────────────────────────────────────────┘
```

**Dependency rules:**
- Layers 1–3 are pure content; no code dependencies between them
- Layer 4 (scripts) depends only on Python stdlib + PyYAML; internal dependency: `package_skill → quick_validate`
- Layer 5 is advisory content consumed by agents, with no code coupling
- No circular dependencies exist

---

## 5. Data Architecture

### Domain Model

The skill-maker operates on a single core domain entity: **a Skill**.

```
Skill (directory)
├── Identity: name (kebab-case, 1-64 chars, matches dir name)
├── Trigger: description (1-1024 chars, no angle brackets)
├── License: optional string
├── Compatibility: optional string (1-500 chars)
├── Metadata: optional string→string map
├── Body: Markdown instructions (≤500 lines, ~5000 tokens)
├── Scripts: executable helpers (Python, Bash, JS)
├── References: on-demand documentation
└── Assets: templates and static resources
```

### Artifacts Produced

| Artifact | Format | Location |
|----------|--------|----------|
| Skill folder | Directory tree | `~/.agent/skills/<name>/` or another client skills directory |
| `.skill` package | ZIP (deflated) | `./dist/<name>.skill` |
| Eval set | JSON | `evals/evals.json` within skill |
| Eval review | HTML | Generated from `assets/eval_review.html` |
| Workspace | Directory tree | `<name>-workspace/iteration-N/` |

### Validation Rules (Data Integrity)

Enforced by `quick_validate.py`:
- Exactly one `SKILL.md` per skill (nested ones rejected)
- Frontmatter is valid YAML with only the 6 recognized fields
- `name`: kebab-case, 1-64 chars, matches parent directory
- `description`: non-empty, ≤1024 chars, no angle brackets
- `compatibility`: ≤500 chars if present
- `metadata`: must be a mapping if present

---

## 6. Cross-Cutting Concerns

### Safety & Governance

Defined in `.agents/instructions/agent-safety.instructions.md`:
- **Fail closed** — deny on ambiguous governance checks
- **Policy as configuration** — YAML/JSON rules, not hardcoded logic
- **Least privilege** — minimum tool access per agent
- **Append-only audit** — immutable audit trails
- Applied via the `allowed-tools` frontmatter field (experimental)

### Content Integrity

From `SKILL.md` body:
- Skills must not contain malware, exploit code, or compromise security
- Actual behavior must not surprise a user who only read the description
- No misleading skills or unauthorized access enablement

### Documentation Management

`.agents/instructions/update-docs-on-code-change.instructions.md` — ensures documentation stays in sync when code changes.

### Markdown Quality

`.agents/instructions/markdown-gfm.instructions.md` — GFM formatting standards for all `.md` files.

### Error Handling

Scripts use a simple pattern:
- `validate_skill()` returns `(False, "error message")` on failure
- `package_skill()` prints emoji-prefixed messages and returns `None` on failure
- Both scripts exit with code 1 on error, 0 on success

### Configuration Management

- No runtime configuration files; behavior is driven by the skill's content
- Environment differences handled via `references/environment-adaptations.md` (capability detection, not env vars)
- `.gitignore` excludes transient artifacts: `__pycache__/`, `*.pyc`, `*.skill`, `dist/`, `*-workspace/`

---

## 7. Technology-Specific Patterns (Python)

### Module Organization

```
scripts/
├── __init__.py          # Empty; makes scripts/ a package
├── quick_validate.py    # Spec validation (zero-network)
├── package_skill.py     # ZIP packaging with validation gate
└── utils.py             # Shared SKILL.md parsing
```

- Run as modules from repo root: `python -m scripts.quick_validate .`
- Internal imports: `from scripts.quick_validate import validate_skill`

### Python Patterns Used

| Pattern | Where | Detail |
|---------|-------|--------|
| Functional returns over exceptions | `validate_skill` | Returns `(bool, str)` tuple instead of raising |
| `pathlib.Path` everywhere | All scripts | No `os.path` usage |
| `re` for frontmatter parsing | `quick_validate.py` | Regex extraction of YAML block |
| `yaml.safe_load` | `quick_validate.py` | Safe YAML parsing (no arbitrary object instantiation) |
| Exclusion lists | `package_skill.py` | Configurable skip patterns for packaging |
| `zipfile.ZIP_DEFLATED` | `package_skill.py` | Standard ZIP compression |

### Dependencies

- **Runtime:** Python 3.8+, PyYAML
- **No dev dependencies** documented (no test framework, linter, or formatter configured)

---

## 8. Testing Architecture

### Evaluation-as-Testing

The project uses a **human-in-the-loop evaluation** model rather than automated unit tests:

1. **Eval cases** (`evals/evals.json`) define prompts and expectations
2. **With-skill runs** execute the skill on cases
3. **Baseline runs** execute without the skill (or with an older version)
4. **Human review** via `assets/eval_review.html` or inline comparison
5. **Iteration** based on qualitative and quantitative feedback

### Test Data Strategy

- Train/holdout splits for description optimization (avoid overfitting)
- Workspace directories (`*-workspace/iteration-N/`) hold per-run outputs
- `eval_metadata.json` per test case tracks assertions

### No Automated Test Suite

The repository contains no `pytest`, `unittest`, or CI test configuration. Testing is by-design a manual process integrated into the skill-creation workflow itself.

---

## 9. Deployment Architecture

### Distribution Model

Skills distribute as directories placed in conventional paths:

| Scope | Path | Override |
|-------|------|----------|
| User-global | `~/.agent/skills/<name>/` | Shared across repositories |
| Client-specific | `.<client>/skills/<name>/` | Varies |

### Packaging

`scripts/package_skill.py` produces a `.skill` ZIP for hosts accepting uploads:
- Validates first (gate: no package without passing validation)
- Excludes: `__pycache__/`, `node_modules/`, `*.pyc`, `.DS_Store`, root-level `evals/`
- Output: `<name>.skill` in specified directory

### No CI/CD Pipeline

No GitHub Actions, no deployment automation. The workflow is manual:
1. Validate: `python -m scripts.quick_validate .`
2. Package: `python -m scripts.package_skill . ./dist`
3. Distribute: copy folder or `.skill` file to target location

---

## 10. Implementation Patterns

### The Progressive Disclosure Pattern

The single most important architectural pattern in this codebase:

```
Tier 1: Metadata (name + description)
  → Always in agent context
  → Budget: name ≤64 chars, description ≤1024 chars

Tier 2: SKILL.md body
  → Loaded on skill activation (description match)
  → Budget: ≤500 lines, ~5000 tokens

Tier 3: Bundled resources (references/, scripts/, assets/)
  → Loaded on explicit demand ("Read spec-reference.md before...")
  → No fixed budget; keep files focused
```

### The Validate-Before-Package Gate

```python
# package_skill.py always validates first
valid, message = validate_skill(skill_path)
if not valid:
    return None  # Block packaging on validation failure
```

### The Exclusion Pattern

Both `quick_validate.py` and `package_skill.py` maintain parallel exclusion lists to keep non-skill content out of validation and packaging:

```python
EXCLUDED_DIR_PARTS = {'__pycache__', 'node_modules'}
ROOT_EXCLUDED_DIR_PARTS = {'evals'}
```

### Frontmatter-as-Contract

The 6-field YAML frontmatter serves as the interface contract between a skill and any agent runtime. The validator enforces this contract strictly — unknown fields are rejected to preserve portability.

---

## 11. Extension and Evolution Patterns

### Adding a New Reference Document

1. Create `references/<topic>.md`
2. Add a pointer in `SKILL.md` body: `"Read references/<topic>.md when <condition>."`
3. Update `README.md` layout section

### Adding a New Script

1. Create `scripts/<name>.py`
2. Import shared utilities from `scripts.utils` if needed
3. Add `if __name__ == "__main__"` for CLI usage
4. Document in `README.md` and `AGENTS.md` common commands
5. Run as: `python -m scripts.<name> <args>`

### Adding a New Instruction Document

1. Create `.agents/instructions/<topic>.instructions.md` with frontmatter (`description`, `applyTo`)
2. Add a forwarder in `.github/instructions/<topic>.instructions.md` for Copilot discovery
3. Reference from `AGENTS.md` canonical instruction documents section

### Adding a New User-Global Skill

1. Create `~/.agent/skills/<skill-name>/SKILL.md`
2. Ensure `name` matches directory name
3. Validate: `python -m scripts.quick_validate ~/.agent/skills/<skill-name>`

---

## 12. Architectural Decision Records

### ADR-1: Content-as-Architecture over Application Code

**Context:** The project enables AI agents to create other skills. The "application" is instructions that agents follow, not code that executes.

**Decision:** Use structured Markdown as the primary architectural artifact, with Python only for deterministic operations (validation, packaging).

**Consequences:**
- (+) Zero runtime dependencies for the core skill behavior
- (+) Portable across any agent that reads Markdown
- (+) Easy to iterate — edit text, not code
- (−) No automated testing of instruction quality
- (−) Behavior varies by agent runtime interpretation

### ADR-2: agentskills.io Standard Conformance

**Context:** Multiple agent platforms exist with different skill formats.

**Decision:** Conform strictly to the open agentskills.io standard; reject non-standard frontmatter fields.

**Consequences:**
- (+) Skills created by skill-maker work across all conformant agents
- (+) Clear validation boundary (6 fields, specific constraints)
- (−) Cannot use platform-specific features without breaking portability
- (−) Must track spec evolution manually (no versioned spec)

### ADR-3: Progressive Disclosure as Core Constraint

**Context:** Agent context windows are finite; loading everything wastes tokens.

**Decision:** Enforce a three-tier loading model with explicit budgets (64/1024 chars metadata, 500 lines body, unlimited but focused references).

**Consequences:**
- (+) Skills scale to complex domains without overwhelming context
- (+) Agents only pay for what they need
- (−) Authors must manually manage the disclosure boundary
- (−) Validator can only check line/token counts, not information density

### ADR-4: Zero-Network Validation Fallback

**Context:** The canonical validator (`skills-ref`) requires network/installation; not always available.

**Decision:** Bundle `quick_validate.py` as a zero-dependency (besides PyYAML) fallback.

**Consequences:**
- (+) Validation works offline, in CI, in any Python environment
- (+) Single source of truth for validation logic within the repo
- (−) Must stay in sync with spec changes manually

### ADR-5: Human-in-the-Loop Evaluation over Automated Tests

**Context:** Skill quality is partially subjective (how well an agent follows instructions).

**Decision:** Use structured human review (eval sets, review HTML, iteration workspaces) instead of automated assertion suites.

**Consequences:**
- (+) Catches quality issues automated tests cannot
- (+) Adapts to any skill domain without custom test infrastructure
- (−) Not runnable in CI
- (−) Requires active human participation for every evaluation cycle

---

## 13. Architecture Governance

### Automated Compliance

- **`quick_validate.py`** — enforces spec compliance on every validate/package run
- **`.gitignore`** — prevents transient artifacts from entering version control
- **Frontmatter allowlist** — rejects unknown fields automatically

### Convention Enforcement

- `AGENTS.md` documents working rules (run as modules, keep SKILL.md lean, progressive disclosure)
- `.agents/instructions/` provides style and safety guardrails
- Directory naming convention (kebab-case matching `name` field) is machine-enforced

### Documentation Practices

- `README.md` mirrors the directory layout with explanations
- `AGENTS.md` serves as the authoritative agent-facing guide
- Reference documents are self-contained and clearly scoped

---

## 14. Blueprint for New Development

### Adding a Feature to the Core Loop

1. Identify which step of the 8-step loop the feature affects
2. If it adds depth, put it in `references/<feature>.md` and add a pointer in `SKILL.md`
3. If it adds automation, create `scripts/<feature>.py` with the `(bool, message)` or `Path | None` return pattern
4. If it adds a new artifact type, document its schema in `references/schemas.md`
5. Update `README.md` layout and `AGENTS.md` common commands
6. Validate: `python -m scripts.quick_validate .`

### Implementation Templates

**New script:**
```python
#!/usr/bin/env python3
"""<One-line description>."""

import sys
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.<name> <args>")
        sys.exit(1)
    # Implementation
    
if __name__ == "__main__":
    main()
```

**New reference document:**
```markdown
# <Title>

<What this document covers and when to read it.>

## <First Section>
...
```

### Common Pitfalls

| Pitfall | Why It Matters |
|---------|---------------|
| Adding non-standard frontmatter fields | Breaks portability; validator rejects them |
| Letting `SKILL.md` grow beyond 500 lines | Wastes agent context; move to references |
| Hardcoding agent-specific behavior | Skill won't port; adapt by capability, not product |
| Skipping validation before packaging | `.skill` will fail on upload |
| Running scripts not as modules | Import paths break (`from scripts.quick_validate` fails) |
| Adding Python dependencies without documenting | Breaks the zero-network promise |

---

## 15. Keeping This Blueprint Updated

This blueprint reflects the repository at commit `c6beb74` (latest as of generation). Update it when:

- New scripts are added to `scripts/`
- New reference documents are added to `references/`
- The agentskills.io spec revision changes (currently `2025-12-18`)
- The progressive disclosure budgets change
- New architectural decisions are made

The architecture is intentionally stable — changes should be infrequent and deliberate.
