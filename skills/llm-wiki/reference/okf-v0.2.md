# OKF v0.2 — condensed normative reference

Distilled from the spec at
`https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md`.
Kept here so the skill works offline. Section numbers match the upstream spec, and
the upstream is what to read where this and it differ.

## Contents

- §2 Terminology · §3.1 Reserved filenames (**and this skill's one declared
  deviation from it**) · §4.1 Frontmatter · §4.2 Body
- §5 Provenance, trust and lifecycle · §6 Cross-linking · §8 Index files · §9 Log
  files
- §10 Attested computations (not used here) · §11 Conformance · §12 Versioning ·
  §13 Changes from v0.1
- Which of this the skill requires, reads and adds

OKF is deliberately tiny: *a directory of markdown files with YAML frontmatter*.
No schema registry, no central authority, no required tooling.

## §2 Terminology

- **Knowledge Bundle** — the directory tree; the unit of distribution.
- **Concept** — one unit of knowledge = one markdown document.
- **Concept ID** — the file's bundle-relative path minus `.md`.
  `architecture/auth.md` → `architecture/auth`.
- **Frontmatter** — YAML block delimited by `---` at the top of the file.
- **Body** — everything after the frontmatter.
- **Source** — a material a concept derives from, recorded in `sources`.
- **Actor** — who or what did something: `<producer>/<version>` for an agent,
  `human:<id>` for a person, `process:<id>` for an automated process (§7).

## §3.1 Reserved filenames

`index.md` and `log.md` have defined meaning at **any** level of the tree and
MUST NOT be used as concept documents. Every other `.md` file is a concept.

> **This skill deviates here, knowingly.** It also exempts `CLAUDE.md`,
> `CLAUDE.local.md` and `AGENTS.md` at any level, so that a bundle can carry the
> instructions for editing it (see A5). By §3.1 those are concepts, and an
> unfrontmattered one fails §11 — so a bundle this skill considers clean is one
> a strict OKF consumer would reject with two untyped concepts. `okf.py` still
> prints *conformant with OKF v0.2*, which is a statement about everything the
> spec covers **minus this exemption**. Nothing else is exempt.

## §4.1 Frontmatter

**`type` is the only required field.** It is a short free-form string
(`Module`, `Decision`, `Playbook`, …). Type values are *not* registered
centrally; consumers MUST tolerate unknown types.

Recommended:

| Field | Meaning |
|---|---|
| `title` | Display name. Consumers MAY derive one from the filename if absent. |
| `description` | One sentence. Feeds `index.md` entries, search snippets, previews. |
| `resource` | URI uniquely identifying the underlying asset. Omit for abstract concepts. |
| `tags` | YAML list of short strings. |

Optional families, all described in §5: `sources`, `generated`, `verified`,
`status`, `stale_after`. Producers MAY add any other keys; consumers SHOULD
preserve unknown keys and MUST NOT reject documents that carry them.

## §4.2 Body

Standard markdown. Producers SHOULD favour **structural** markdown — headings,
lists, tables, fenced code — over freeform prose, because structure aids both
human reading and agent retrieval.

No body sections are required. Conventional headings: `# Schema` (an asset's
columns or fields), `# Examples`, and `# Computation` (§10). **There is no
`# Citations`**: attribution to a source is a footnote keyed to a `sources` entry
(§5.1).

## §5 Provenance, trust and lifecycle

All optional, and their absence carries meaning without ever causing a rejection.
Every timestamp-valued key is an ISO 8601 datetime with an explicit UTC offset,
`2026-06-30T14:00:00Z`.

### §5.1 `sources`

A list of the materials a concept derives from. Each entry is a **mapping**:

```yaml
sources:
  - id: rfc7519                     # optional; the key a footnote cites
    resource: https://www.rfc-editor.org/rfc/rfc7519   # REQUIRED
    title: JSON Web Token           # optional
    author: team:ietf               # optional credibility signals:
    usage_count: 5000               #   author, usage_count, last_modified
    last_modified: 2026-05-30T00:00:00Z
usage_window: { from: 2026-06-01T00:00:00Z, to: 2026-06-30T00:00:00Z }
```

`resource` names either something a consumer can follow — an absolute URL, a
bundle-relative path, a path into `references/` — **or a scope descriptor it
cannot** (for example `all queries in BigQuery project X`). Lineage is
expressed by links, not a field. Per-claim attribution is a markdown footnote
whose label is the `id`: `…sharded daily.[^rfc7519]`, then `[^rfc7519]: JSON Web
Token`. Labels are keyed rather than positional so that a reordered list does not
silently misattribute.

### §5.2 `generated` and `verified`

`generated: { by: <actor>, at: <datetime> }` records how the current content was
produced; `at` is the last meaningful change. `verified` is a list of
`{ by, at }` events confirming the content against its sources (a bare mapping is
a one-element list). They are kept apart because who *wrote* a concept need not be
who *confirmed* it.

### §5.3 Trust tiers

Derived from `verified`, lowest first: no `verified` ⇒ unverified; only non-`human:`
actors ⇒ machine-confirmed; a `human:` actor ⇒ human-reviewed. Advisory, never
access control.

### §5.4 `status`

`draft | stable | deprecated`. `draft` is unreviewed or incomplete; `stable` is the
default when absent; `deprecated` is kept for links and history and is no longer
current.

### §5.5 `stale_after`

An absolute instant: a concept is stale when `now >= stale_after`. Absolute, not a
TTL, so the decision is a plain comparison.

## §6 Cross-linking

Plain markdown links — **not** `[[wikilinks]]`. Two forms:

- **Absolute (bundle-relative)** — begins with `/`, resolved from the bundle
  root: `[customers](/tables/customers.md)`. **Recommended**: survives moving
  the *linking* document.
- **Relative** — `[sibling](./other.md)`.

A link asserts an untyped relationship; the *kind* of relationship is conveyed
by surrounding prose, not the link. Consumers **MUST tolerate broken links** — a
link to a missing target is not malformed, it may simply be knowledge not yet
written. (So forward-referencing a concept you intend to write is legal.)

Path-valued fields (`resource`, `sources[].resource`) take an absolute URL, a
`/`-prefixed bundle-relative path, or a relative path. A `references/`
subdirectory conventionally mirrors external material as concepts.

## §8 Index files

`index.md` MAY appear in any directory. It enumerates that directory's contents
to support **progressive disclosure** — letting a reader or agent see what
exists before opening anything.

Index files **contain no frontmatter**, with exactly one exception: the
bundle-root `index.md` MAY declare `okf_version: "0.2"` (§12).

Body is one or more `#` sections of bullets:

```markdown
# Section / Group Heading

* [Title 1](relative-url-1) - short description of item 1
* [Subdirectory](subdir/) - short description of the subdirectory
```

Entries SHOULD reuse the linked concept's `description`. Producers MAY generate
indexes; consumers MAY synthesize one when absent.

## §9 Log files

`log.md` MAY appear at any level to record changes to that scope. Flat,
date-grouped, **newest first**. Date headings MUST be ISO 8601 `YYYY-MM-DD`.

```markdown
# Directory Update Log

## 2026-05-22
* **Update**: Added new table reference for [Customer Metrics](/tables/customer-metrics.md).
* **Creation**: Established the [Dataplex Playbook](/playbooks/dataplex.md).
```

The leading bold word (`**Update**`, `**Creation**`, `**Deprecation**`) is
convention, not requirement.

## §10 Attested computations

A concept of `type: Attested Computation` carries a sanctioned way to compute a
value, with `runtime`, `parameters`, `computation`, `executor` and `attester`
keys, so a consumer can confirm a value was produced by running it. This skill
neither writes nor reads them; see the upstream spec.

## §11 Conformance

A bundle is conformant if:

1. Every non-reserved `.md` file has a parseable YAML frontmatter block.
2. Every frontmatter block has a non-empty `type`.
3. Every `index.md` / `log.md` present follows §8 / §9.

Consumers MUST NOT reject a bundle for: missing optional fields, unknown `type`
values, unknown extra frontmatter keys, broken cross-links, or missing
`index.md`. This permissiveness is intentional — bundles grow, get refactored,
and are partly agent-generated.

## §12 Versioning

`<major>.<minor>`. Minor = backward-compatible additions. Major = breaking.
Declare the target version via `okf_version: "0.2"` in the root `index.md`
frontmatter. Consumers that do not understand a declared version SHOULD attempt
best-effort consumption rather than refusing the bundle.

## §13 Changes from v0.1

Two deliberate breaking changes; the rest is additive.

- **`timestamp` is superseded by `generated.at`.** A consumer MAY fall back to a
  legacy `timestamp`.
- **The body `# Citations` list is superseded by `sources`.** A consumer MAY still
  parse a legacy `# Citations` list.
- New: the `sources`, `generated`, `verified`, `status` and `stale_after`
  families, the actor convention, and `Attested Computation`.

## What this skill requires, reads and adds

- **Requires** what §11 requires, and nothing more: `type`. `lint` also asks for a
  `description` inside a budget (an extension, `W013`/`W017`).
- **Reads** `sources` (each entry's `resource`, when it names files in the
  repository), `status` (`deprecated` sinks a page in its index), `okf_version`,
  and legacy `timestamp` not at all. It reads `generated`, `verified` and
  `stale_after` not at all, and keeps them if a page has them.
- **Adds**, as producer extensions §4.1 allows: `sources_digest`,
  `superseded_by`, `amends`, `amended_by`, and the `Decision`, `Invariant`,
  `Module`… `type` vocabulary of `concept-types.md`.
- **Leaves out** `generated.at` and `timestamp` on purpose: a date written by hand
  is wrong a week later, and `git log -1 --format=%cI -- <page>` says it.
