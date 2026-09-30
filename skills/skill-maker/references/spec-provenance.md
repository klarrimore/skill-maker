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
3. **Skill-maker hardening**: an extra check in this repo's bundled validator
   (`quick_validate.py`). These checks are stricter than the spec and are explicitly not
   spec requirements. The validator rejects angle brackets in `description`, rejects the
   em dash character (U+2014) anywhere in `SKILL.md`, rejects fields outside the six, and
   rejects more than one `SKILL.md`. It warns on the 500-line and 5000-token body budgets.
   Treat these as house rules, not standard rules.

A skill can pass the spec and fail hardening. Say which one you are enforcing.

## Versioning

The spec publishes no version number, tag, or changelog. Conformance is defined by the
current spec text. This is an inference from absence, not a stated intent. Do not assert a
release date as authoritative. Re-read the current spec text instead of trusting a
snapshot date.

The history shows only wording, example, and field-table clarifications. No frontmatter
field was added or removed. The project maintains a high bar for additions, so the field
set is stable in practice.

## Spec versus `skills-ref`

The reference validator differs from the spec text in these known ways. The research
investigation's "Important gaps between validator behavior and spec text" records them.
The validator is not a second spec.

- The validator rejects top-level fields outside the six. The spec never forbids extra
  fields; it says extra properties belong in `metadata`. Store extras in `metadata`.
- The validator enforces the `compatibility` upper bound of 500 but not the minimum of 1.
  An empty string passes validation.
- The validator does not type-check `allowed-tools`, even though the spec calls it a
  space-separated string.
- The validator accepts lowercase `skill.md`. The spec always writes `SKILL.md`. Use the
  uppercase name for portability.
- The validator normalizes NFKC and accepts any Unicode `isalnum()` name. The spec prose
  says "unicode lowercase alphanumeric" while its parenthetical says `a-z, 0-9`. This
  inconsistency is unresolved. The validator accepts Chinese, Russian, and accented names.
- The validator does not check body length, line counts, or reference depth. Those are
  recommendations, not validation rules.
- The validator does not check for angle brackets. The bundled validator does. That is
  hardening.

## `skills-ref` status

Treat `skills-ref` as a reference and demonstration library, not a stable dependency.

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

- **Angle-bracket rejection.** The spec is silent, and `skills-ref` does not check it. That
  part is unchanged: this is not an agentskills.io requirement anywhere. It is not an
  isolated invention of this skill's own validator, though: both Anthropic's and OpenAI's own
  official skill-authoring tools apply the identical check (same function name, same control
  flow, same error string), which is strong evidence of one shared `skill-creator`-style
  tooling lineage rather than independent inventions. Neither of those clients' actual
  runtimes enforce it; only their authoring-time tooling does, the same way this skill's
  bundled validator is hardening applied at authoring time, not a runtime guarantee. Treat
  the check as inherited, cross-client authoring-tool hardening, not a spec requirement and
  not proof any runtime rejects angle brackets.
- **Reserved words in names.** The standard defines no reserved-word list, and that remains
  true of agentskills.io itself. It is no longer undocumented everywhere: Claude's own
  platform documentation names its reserved substrings for `name` outright (its own product
  and vendor name, "anthropic" and "claude"), and Claude Code separately reserves the
  skill-folder names `synced` and `anthropic-skills`. Client-side rejection on this axis is
  real and citable for that one client; still check each client you target rather than
  assuming the list generalizes.
- **`~/.agent/skills/` (singular).** The client guide lists `~/.agents/skills/` (plural).
  The singular path is unverified.
- **Zipped `.skill` uploads.** The spec defines folders, not archives, and no agentskills.io
  page mentions `.skill`. That half still holds. It is not unattested everywhere: Anthropic's
  own official skill-authoring tooling defines and produces this exact format (a
  `ZIP_DEFLATED` archive rooted at the skill folder's own contents, validated before
  zipping). Treat `.skill` as a real, client-specific packaging convention with a first-party
  source on that one client, not as an open-standard requirement.
- **Ecosystem commands.** `gh skill` and `npx skills add <owner/repo>` do not appear in the
  first-party docs. They are ecosystem tooling, not standard behavior.
- **`metadata.version`.** The spec defines no `version` field and no versioning scheme.
  `metadata` is an arbitrary key-value map. Do not treat `version` as a spec field.
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
- **Security.** The spec is silent on security. Project-level trust checks and dependency
  caution are sound advice, not spec statements.

## How to read a rule

When the standard and a validator differ, name the one you follow. Say "the spec requires"
only for text in `docs/specification.mdx`. Say "for portability" for cross-client
guidance. Say "our validator hardens this" for the bundled checks. Never let a validator's
behavior pass as a spec requirement.
