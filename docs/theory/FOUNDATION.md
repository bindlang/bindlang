# bindlang Foundation

---

## Overview

bindlang implements **deferred semantic binding** as a Python library.

It starts from a simple idea: sometimes meaning should not be decided at definition time, but only when the right context is available.

---

## Core Theory: Latent/Bound Semantics

### Fundamental Concepts

**Latent** – Semantic potential. The interpretation method (_how to read this symbol_) is defined, but the concrete meaning (_what it does_) is undecided until context arrives.

**Bound** – Semantic resolution. Context supplies the missing conditions (who, when, where, system state), allowing the latent symbol to acquire a determinate meaning.

**Transition**

`Latent → [context evaluation] → Bound`
(or remains Latent if the conditions are not met)

---

## Semantic Dimension

Deferred semantic binding functions as a fourth semantic axis, orthogonal to familiar distinctions:

- True / False
- Defined / Undefined
- Null / Value
- **Latent / Bound** (contextual activation)

### Key Principle

bindlang does **not** defer when something executes.  
It defers **what** becomes true, valid, or actionable.

---

## A Simple Voting Analogy

A cast but uncounted ballot expresses intent but has no definite effect until the tallying context resolves it. The meaning exists, but only in potential form.

bindlang generalizes this pattern: latent symbols encode structured intent, and their concrete effect on world state is determined only at binding time under a specific context.

---

## Context Evaluation Framework

Meaning is evaluated through four contextual dimensions:

1. **Who** – identity, role, trust level
2. **When** – order, timing, temporal conditions
3. **Where** – domain, scope, location
4. **State** – system conditions, mode, modality

### Example: Same Symbol, Different Contexts

`⟦VOTE:promote⟧`

**Admin context**

- Weight 2.0
- Immediate effect
- No validation required

**New user context**

- Weight 0.5
- Deferred effect pending checks
- Validation required

**Blocked context**

- Weight 0.0
- No effect
- No validation

Same symbol. Meaning shifts entirely with context.

---

## Symbol Notation & Types

### Notation

`⟦TYPE:parameter⟧` – explicit carrier of latent semantic intent.

### Symbol Classes

**Gates** – conditions that determine whether activation is allowed.

- Evaluate to boolean.
- Must pass before any event can run.

**Events** – actions that occur upon activation.

- Execute only after all relevant gates have passed.
- Carry the semantic payload.

---

## Symbol Lifecycle

Concrete symbol instances follow a lifecycle:

```text
Definition → Latent → [Gate Evaluation] → Activated → Bound → Archived
                                     ↘ Failed → Expired
```

- **Definition** – a reusable interpretation template.
- **Latent** – a concrete ticket that _may_ bind later.
- **Bound** – successfully activated under a specific context.
- **Archived** – no longer eligible for activation.
- **Failed / Expired** – could not activate due to violated or outdated conditions.

bindlang tracks not only what happened, but also what **could have** happened.

---

## Symbol Consumption & Reuse Semantics

Latent symbols act as **binding tickets**: concrete opportunities to realize an effect under suitable conditions.
One practical concern is avoiding situations where the _same ticket_ is applied multiple times in ways that no longer make semantic sense.

### One-Shot Tickets

Some performatives are intrinsically single-use:

- `⟦MARRY:couple⟧`
- `⟦APPROVE:invoice⟧`
- `⟦SIGN:contract⟧`

Once such a symbol has bound and its effect has been applied, that specific ticket is spent. Re-using the exact same instance would misrepresent what actually happened.

### Reusable Contracts

Other patterns behave more like standing rules:

- If `temp > 30°C` → turn on fan
- If `submissions_open=true` → notify reviewers
- If `has_weapon=true` → allow `attack`

Here, the _definition_ persists as a reusable contract. Each time the gate conditions are satisfied, a new activation takes place and a new event instance is produced.

bindlang makes this distinction explicit:

- **Symbol definitions** – reusable templates for interpretation and effect
- **Symbol instances** – individual tickets that participate in the lifecycle above

This clarifies when a specific semantic commitment is consumed once, and when it is allowed to fire repeatedly under changing context.

---

## Foundation Symbol Library

bindlang extends ideas from speech-act theory: performative meaning becomes a runtime computation over identity, time, and system state.

### Symbol examples (illustrative)

| Symbol             | Description                                | Context Sensitivity |
| ------------------ | ------------------------------------------ | ------------------- |
| `⟦VOTE:promote⟧`   | Promotional voting with adaptive semantics | Who, When, State    |
| `⟦WITNESS⟧`        | Quorum-based attestation                   | Who, When           |
| `⟦GATE:sec_clean⟧` | Security gating with conditional cleanup   | Who, State          |
| `⟦TRUST:target⟧`   | Trust scoring and evaluation               | Who, When           |
| `⟦CASCADE:viral⟧`  | Propagation trigger                        | Who, When           |
| `⟦DECAY⟧`          | Temporal fading                            | When, State         |

---

## References

- Theoretical foundation – [https://dsbl.dev/dsbl-framework.html](https://dsbl.dev/dsbl-framework.html)
- Latent/Bound – [https://dsbl.dev/latentbound.html](https://dsbl.dev/latentbound.html)
