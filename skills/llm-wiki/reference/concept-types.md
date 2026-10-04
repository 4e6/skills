# Concept types & templates for a codebase wiki

## Contents

- **Pick the type** — the order to reach for them in, ending at `Decision`, which
  has a gate.
- **The types** — every `type`, its half-life, what it answers, and its
  directory.
- **`Decision` or `Module`?** — what a `Decision` is, what is neither, and what to
  do to an older page whose prose a change has passed by.
- **Templates** for seven of the twelve types: Decision (ADR), Invariant, Module,
  Gotcha, Playbook, Glossary Term, Open Question. The rest — `Integration`,
  `Data Model`, `Convention`, `Overview`, `Reference` — have none; follow the
  frontmatter contract and the nearest template.

OKF leaves `type` free-form (§4.1). This is the vocabulary this skill uses. Stick
to it unless the project genuinely needs a new kind — a consistent `type` set is
what makes `index.md` grouping and type-filtered retrieval useful.

## Pick the type

Ask in this order and stop at the first yes. If a proposed page doesn't fit any
of them, that is a strong hint it belongs in the code, not the wiki.

1. **Does something have to hold, and break if it doesn't?** `Invariant`.
2. **Did it cost somebody an afternoon, and will it again?** `Gotcha`.
3. **Is it what a word means here?** `Glossary Term`.
4. **Is it how to do a task, step by step?** `Playbook`.
5. **Is it what a part of the project is for, where its edges are, or why it is
   shaped so?** `Module` — and the *why*, with the alternatives it turned down, goes
   in that page's `# Why` and `# Rejected alternatives` sections.
6. **Is it a fork, taken, between alternatives weighed, that no single page
   owns?** Only then a `Decision`, and only through the gate in SKILL.md A2.

`Decision` comes last on purpose. It looks the most like what was asked for when
the request says *record why* and a directory is named after it, and so it is the
page agents write when the thing they have is a reason. A reason belongs to the
page it explains.

## The types

Each type below is listed with its **knowledge half-life** — how long the content
stays true.

| `type` | Half-life | Answers | Directory |
|---|---|---|---|
| `Invariant` | years | *What must always hold?* | `invariants/` |
| `Gotcha` | years | *What bites people?* | `gotchas/` |
| `Glossary Term` | years | *What does this word mean here?* | `domain/` |
| `Integration` | months | *How do we talk to this third party?* | `integrations/` |
| `Data Model` | months | *What is stored, and what does it mean?* | `domain/` |
| `Playbook` | months | *How do I do this operational task?* | `playbooks/` |
| `Convention` | months | *How do we write code here?* | `conventions/` |
| `Module` | weeks | *What is this for, where are its edges, and why?* | `architecture/` |
| `Overview` | weeks | *What is this project?* | bundle root |
| `Open Question` | short | *What don't we know yet?* | `questions/` |
| `Decision` | years while its subject lives | *Which fork was taken, and what was rejected?* — **gated** | `decisions/`, created when a page passes |
| `Reference` | — | mirrored external material backing a citation | `references/` |

`Module` and `Overview` have the shortest half-life of the durable types, so they
are the ones the sync loop touches most. Keep them about **responsibility,
boundaries and the reasoning behind both**, never about function signatures.

## `Decision` or `Module`?

**A `Decision` is written about something that already happened.** It records a
fork taken, under the constraints in play at the time, and it is dated and
numbered because both of those are claims about a moment. An ADR for a design
that has not been built is a plan with a permanent number on it. **A decision that
names no alternative it turned down is not a decision**, whatever else it is: with
nothing to re-litigate it is a description, and it belongs in the page it
describes. `lint` warns (`W019`) below two alternatives, and again (`W021`) when
Decisions make up more than a fifth of the concepts.

**Changing something already decided is usually neither.** The test is
entailment: **does an existing `Decision` already commit the project to this
outcome?** If it does, the work implements that decision rather than taking one,
and the rule that now has to hold is an `Invariant`. Weighing alternatives is not
deciding either: refusing to overturn a decision leaves it standing. Work that
only moves which cases fall which side of a rule an existing decision settles
gets no ADR; work that settles something the earlier page left open does, so
**narrowing or widening a decision's scope is a fork whenever the earlier page
did not already commit to the new scope**.

**A decision overtaken by events** has a sentence that is no longer true, the
mechanism it happened to describe. It stays frozen: correct it in place with a
short note saying which claim has been passed by and where the live answer is, and
leave its number, status and reasoning alone. A note is not an amendment; reach
for `amends`/`amended_by` only when a new page actually revises what the old one
decided.

**A `Module` carries the argument for behaviour nobody forked over** — why the
boundary falls there, which case it was drawn around, what it costs — and the
alternatives it turned down, in `# Rejected alternatives`. That is the usual home
of a *why*. A fork that spans modules and that someone might genuinely reopen gets
a `Decision`, and the modules link to it in a short `# Decisions` section, so
superseding one does not strand the other.

---

## Templates

### Decision (ADR)

**Only after the gate in SKILL.md A2**: a fork taken, two alternatives weighed and
named, no single page that owns it, and the user's yes. Otherwise it is a `# Why`
section of the page that owns the thing.

Immutable once accepted. Never rewrite the reasoning of an accepted decision —
supersede it with a new one and cross-link both. Retire it once its subject is
gone (SKILL.md A6).

```markdown
---
type: Decision
title: Use JWTs for service-to-service auth
description: Chose stateless JWTs over a shared session store for internal RPC.
status: accepted            # proposed | accepted | amended | superseded
tags: [auth, security]
timestamp: 2026-07-10T09:00:00Z
sources: [src/rpc/**]       # the code the choice shaped; when it is gone, so is the page's subject
superseded_by: /decisions/0009-mtls.md   # only when status: superseded
---

# Context

What forced a choice. Constraints in play at the time.

# Alternatives considered

Each names the constraint that ruled it out. Two at least, and a straw one does
not count.

* **Shared session store** — rejected because it puts a Redis dependency on the
  hot path.
* **mTLS** — rejected because there is no cert rotation story yet. See [open
  question](/questions/cert-rotation.md).

# Decision

What we chose, stated in one sentence.

# Consequences

What this makes easy, and what it makes hard. Include the bill: what we now
have to live with.
```

Filename: `NNNN-kebab-slug.md`, zero-padded, monotonic. Never renumber.

### Invariant

The highest-value, lowest-maintenance page type. A property the code must
uphold, plus how it is enforced and what breaks if it isn't.

```markdown
---
type: Invariant
title: Every order has exactly one payment intent
description: Orders and payment intents are 1:1; a second intent means a bug upstream.
tags: [billing]
timestamp: 2026-07-10T09:00:00Z
sources: [src/billing/**]
source_commit: 4f2a1c9e...
---

# Statement

For every row in `orders`, exactly one `payment_intent` exists.

# Why

Stripe charges idempotently per intent. Two intents = double charge.

# Enforced by

* Unique constraint `payment_intents.order_id`.
* [Charge module](/architecture/billing.md) creates the intent inside the order transaction.

# If violated

Customers are double-charged. See [refund playbook](/playbooks/refunds.md).
```

### Module

Responsibility and edges. **No signatures, no line numbers, no file trees** —
those are what the code is for, and they rot within days. Keep the reasoning
here, in `# Why this shape`, with what was turned down in `# Rejected
alternatives`; a `Decision` page is for a fork that spans modules. See
[`Decision` or `Module`?](#decision-or-module).

```markdown
---
type: Module
title: Auth
description: Issues and verifies sessions for the web and mobile clients.
tags: [auth]
timestamp: 2026-07-10T09:00:00Z
sources: [src/auth/**]
source_commit: 4f2a1c9e...
---

# Responsibility

Owns session issuance, verification, and revocation. Does **not** own user
records — that is [accounts](/architecture/accounts.md).

# Boundaries

* Everything outside this module reaches auth through `verifySession()`. No
  other module reads the session cookie directly.
* Talks to [Redis](/integrations/redis.md) for the revocation list only.

# Why this shape

Sessions are stateless JWTs, so a verifier needs no round trip to the issuer.
Revocation is the cost: it is a list, checked on each request.

# Rejected alternatives

* **Shared session store** — rejected because it puts a Redis dependency on the
  hot path of every request.
* **Long-lived tokens with no list** — rejected because a leaked token could not
  be revoked.

# Invariants

* [Sessions are revocable within 30s](/invariants/session-revocation.md)

# Gotchas

* [Clock skew breaks JWT verification](/gotchas/clock-skew.md)
```

### Gotcha

Hard-won knowledge that cost someone an afternoon. Cheap to write, enormous
payoff, essentially never goes stale.

```markdown
---
type: Gotcha
title: Clock skew breaks JWT verification
description: Hosts more than 60s ahead of the issuer reject freshly minted tokens.
tags: [auth, ops]
timestamp: 2026-07-10T09:00:00Z
---

# Symptom

`TokenNotYetValid` on a token that was just issued.

# Cause

`nbf` is checked against local time; our issuer and verifier are different hosts.

# Fix

Ensure `chrony` is running. We allow 60s leeway, not more — see
[auth module](/architecture/auth.md).
```

### Playbook

```markdown
---
type: Playbook
title: Rotate the signing key
description: Steps to rotate the JWT signing key without logging everyone out.
tags: [oncall, auth]
timestamp: 2026-07-10T09:00:00Z
---

# When

Quarterly, or immediately on suspected compromise.

# Steps

1. Add the new key to `JWT_KEYS` as a *verification* key. Deploy. Wait one TTL.
2. Promote it to the signing key. Deploy.
3. Remove the old key after one TTL.

# Verification

`curl /healthz/jwt` reports the active `kid`.
```

### Glossary Term

```markdown
---
type: Glossary Term
title: Settlement
description: The point at which funds irrevocably move, distinct from authorization.
tags: [billing, domain]
timestamp: 2026-07-10T09:00:00Z
---

Authorization reserves funds; **settlement** moves them. Our `orders.status`
says `paid` at *authorization*, not settlement — a naming wart we kept for
backward compatibility. See [orders](/architecture/orders.md#why-this-shape).
```

### Open Question

Explicitly recording what you don't know is what stops the wiki from
confabulating. When it is answered, set `status: answered` and write the answer
where it belongs — a `Decision` only if answering it took a fork, and otherwise
an `Invariant`, a `Module` or whichever type the answer is. `okf.py` sinks an
answered question under *No longer current* rather than deleting it: it is still
a true record of what was once unknown.

```markdown
---
type: Open Question
title: How do we rotate mTLS certs?
description: No rotation story exists; blocks the mTLS decision.
status: open
tags: [security]
timestamp: 2026-07-10T09:00:00Z
---

# Question

Blocks [mTLS](/architecture/auth.md#rejected-alternatives). Nobody has owned this.
```
