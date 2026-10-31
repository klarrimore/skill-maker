# Spec Provenance and Authority

This file is the companion to `spec-reference.md`. Read it when you need to know where a
rule comes from and how much authority it carries. `spec-reference.md` states the rules;
this file states their source and tier.

Claims in this ecosystem come from three layers. The layers disagree in places. Before you
enforce a rule, identify its layer.

## The three authority tiers

- **Spec-mandated**: text in `docs/specification.mdx`. This file is authoritative for
  format requirements.
- **Documented recommendation**: the `/skill-creation/` and `/client-implementation/`
  guides. These advise skill authors and client implementors.
- **Implementation behavior / de-facto convention**: what `skills-ref` does, and what
  clients happen to share. These do not add normative requirements.

The standard's repository `AGENTS.md` states both points directly. It says
`docs/specification.mdx` is authoritative for format requirements. It also says
explanatory documentation, examples, tests, and implementations do not add requirements.
Under this rule, `skills-ref` behavior is a demonstration, not a second spec.

## The three-way rule taxonomy

Apply this taxonomy to every rule you meet:

1. **Spec constraint**: a requirement stated in `docs/specification.mdx`. Example: the
   `name` field is required and at most 64 characters. Treat these as mandatory for
   conformance.
2. **Portability rule**: guidance from the guides, or from cross-client convention. It
   decides whether a skill runs across clients, not whether the spec accepts it. Example:
   extra top-level fields are spec-tolerated but not portable.
3. **Skill-maker hardening**: a check the bundled validator (`scripts/quick_validate.py`)
   adds that neither the spec nor `skills-ref` requires. Treat these as house rules,
   stricter than the standard.

A skill can pass the spec and fail hardening.

## Bundled validator checks by tier

Each check the bundled validator performs carries exactly one tier. Severity is for strict
mode; how import mode treats each check is in `spec-reference.md` "Validation: strict versus
import". Strict mode enforces all three tiers, so a strict pass means spec-conformant,
portable, and hardened.

| Check | Tier | Strict severity | Source |
| --- | --- | --- | --- |
| `SKILL.md` exists | Spec constraint | Error | Spec directory structure |
| Frontmatter is a YAML mapping | Spec constraint | Error | Spec: YAML frontmatter, then Markdown |
| Exactly one `SKILL.md` | Skill-maker hardening | Error | House rule: one entry point per packaged skill |
| `name` present and a non-empty string | Spec constraint | Error | Spec field table |
| `name` character set and hyphens | Spec constraint | Error | Spec field table (Unicode reading: see `spec-reference.md`) |
| `name` at most 64 characters | Spec constraint | Error | Spec field table |
| `name` matches the directory | Spec constraint | Error | Spec field table |
| `description` present and a non-empty string | Spec constraint | Error | Spec field table |
| `description` at most 1024 characters | Spec constraint | Error | Spec field table |
| `license` is a string | Spec constraint | Error | Spec field table |
| `allowed-tools` is a string | Spec constraint | Error | Spec field table (space-separated string) |
| `compatibility` a string of at most 500 characters | Spec constraint | Error | Spec field table (upper bound only) |
| `metadata` maps strings to strings | Spec constraint | Error | Spec field table |
| Only the six spec fields | Portability rule | Error | Spec places extras in `metadata`; `skills-ref` rejects them |
| No angle brackets in `description` | Skill-maker hardening | Error | Inherited authoring-tool check (see below) |
| No em dash in `SKILL.md` | Skill-maker hardening | Error | House style |
| Body under 500 lines | Skill-maker hardening | Warning | Spec recommendation that `skills-ref` leaves unchecked |
| Body under about 5000 tokens | Skill-maker hardening | Warning | Spec recommendation that `skills-ref` leaves unchecked |
| Body under 8000 bytes (Codex) | Skill-maker hardening | Warning | Codex default body truncation, as of 2026-09-30 |
| `description` under 973 characters | Skill-maker hardening | Warning | Margin under the spec's 1024 limit |
| ASCII-only `name` | Skill-maker hardening | Warning | One client's authoring validator accepts only `^[a-z0-9-]+$` |

## Versioning

The spec publishes no version number, tag, or changelog. Conformance is defined by the
current spec text. This is an inference from absence, not a stated intent. Re-read the
current spec text whenever a rule's authority matters; a snapshot date carries no authority.

The history shows only wording, example, and field-table clarifications. No frontmatter
field was added or removed. The project maintains a high bar for additions, so the field
set is stable in practice.

## Spec versus `skills-ref`

The reference validator differs from the spec text in these known ways. The validator is
not a second spec.

- `skills-ref` rejects top-level fields outside the six. The spec never forbids extra
  fields; it says extra properties belong in `metadata`.
- `compatibility` minimum: `skills-ref` enforces only the 500 upper bound (rule:
  `spec-reference.md` compatibility rules).
- `skills-ref` does not type-check `allowed-tools`, even though the spec calls it a
  space-separated string.
- `skills-ref` accepts lowercase `skill.md`. The spec always writes `SKILL.md`. Use the
  uppercase name for portability.
- Unicode names: `skills-ref` normalizes NFKC and accepts Unicode names (rule and spec
  ambiguity: `spec-reference.md` name rules).
- `skills-ref` does not check body length, line counts, or reference depth; the spec states
  them as recommendations.

## `skills-ref` status

Treat `skills-ref` as a reference and demonstration library, not a stable dependency. It
exposes `validate`, `read-properties`, and `to-prompt`.

- Its `README.md` says it is not meant to be used in production.
- `CONTRIBUTING.md` says the project is still determining the library's direction and is
  not accepting code contributions right now.
- The canonical install path is a local editable install (`pip install -e .`).
- The PyPI artifact has provenance discrepancies. Its advertised CLI is `agentskills`,
  not `skills-ref`. Its URLs point at the old organization, and its owner is an
  individual. Verify provenance before you depend on it.

## Unverified and de-facto claims

The primary sources do not verify the following claims. Treat them as de-facto knowledge,
or as client-specific behavior, and check a client's docs before relying on them.

- **Angle-bracket rejection.** The spec is silent, `skills-ref` does not check it, and no
  agentskills.io source requires it. Anthropic's and OpenAI's official skill-authoring tools
  both apply the identical check (same function name, same control flow, same error string),
  which points to one shared `skill-creator`-style tooling lineage. Their runtimes do not
  enforce it; only their authoring-time tooling does, as with this skill's bundled validator.
  Treat the check as inherited, cross-client authoring-tool hardening, not a spec requirement
  and not proof that any runtime rejects angle brackets.
- **Reserved words in names.** Client-specific: the standard defines no list, and Claude's
  platform documentation is the first-party source for one client's (rule:
  `spec-reference.md` name rules).
- **`~/.agent/skills/` (singular).** The client guide lists `~/.agents/skills/` (plural).
  The singular path is unverified.
- **Zipped `.skill` uploads.** The spec defines folders, not archives, and no agentskills.io
  page mentions `.skill`. Anthropic's official skill-authoring tooling defines and produces
  the format (a `ZIP_DEFLATED` archive rooted at the skill folder's own contents, validated
  before zipping). Treat `.skill` as a client-specific packaging convention with a
  first-party source on that one client, not as an open-standard requirement.
- **Ecosystem commands.** `gh skill` and `npx skills add <owner/repo>` do not appear in the
  first-party docs. They are ecosystem tooling, not standard behavior.
- **`metadata.version`.** The spec defines no `version` field and no versioning scheme.
  `metadata` is an arbitrary key-value map, so `version` is an ordinary `metadata` key.
- **Skill-to-skill composition.** The docs never discuss composition. "Unsupported" is an
  inference from silence, not a documented prohibition.
- **Client extension fields.** `context: fork`, `user-invocable`, `model`, and
  `agents/openai.yaml` do not appear on agentskills.io. `disable-model-invocation` does
  appear once, as a worked example in the first-party client guide
  (`adding-skills-support.mdx`), but it is not a spec-defined field there or anywhere else
  first-party. None of these are spec fields; verify each against the relevant client's own
  docs.
- **Token counts.** The spec says about 100 tokens for tier 1; the client guide says about
  50 to 100. Tier 2 is "under 5000 tokens recommended." Exact tokenization is
  model-dependent, and the spec names no tokenizer.

## How to read a rule

When the standard and a validator differ, name the one you follow. Say "the spec requires"
only for text in `docs/specification.mdx`. Say "for portability" for cross-client
guidance. Say "our validator hardens this" for the bundled checks. Label every validator
behavior as the validator's, so a reader can always tell it from a spec requirement.
