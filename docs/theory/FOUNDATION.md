# bindlang Foundation

**Deferred Semantic Binding for Python**

---

## Project Vision

bindlang implements deferred semantic binding - portable semantic contracts where meaning remains latent until context activates it.

**Applications:**

- Narrative compression
- Multi-agent coordination
- Approval workflows with audit trails
- Context-dependent authorization

---

## Core Theory: Latent/Bound Semantics

### Fundamental Concepts

**Latent**: Meaning that waits. A state of semantic potential where the interpretation method (HOW) is defined, but the concrete meaning (WHAT) awaits context.

**Bound**: Meaning fixed by context. A semantic state where context has provided the necessary conditions (who, when, where, state), transforming latent potential into concrete meaning.

**Transition**: `Latent → [context evaluation] → Bound` (or remains Latent if conditions aren't satisfied)

### The Fourth Semantic Dimension

Deferred Semantic Binding operates as a fourth orthogonal semantic dimension, alongside:

- **True/False** (logic)
- **Defined/Undefined** (existence)
- **Null/Value** (content)
- **Latent/Bound** (contextual activation) ← NEW

### Key Principle

Rather than deferring _when_ something executes (like promises or lazy evaluation), bindlang defers _what_ gets determined. This is fundamentally different from existing computational abstractions.

### The Sealed Ballot Analogy

A cast but uncounted vote carries voter intent yet remains neither true nor false in the tally. The meaning emerges only during counting - the context provides the conditions for semantic binding.

bindlang generalizes this pattern: latent symbols carry structured intent, but their concrete effect on world state exists only at the moment of binding under a specific context.

---

## Context Evaluation Framework

Meaning doesn't exist independently but depends on runtime evaluation of **four contextual dimensions**:

1. **Who** - Participant/identity/agent
2. **When** - Time/sequence/ordering
3. **Where** - Domain/location/scope
4. **State** - Modality/quality/system conditions

### Example: Same Symbol, Different Contexts

The symbol `⟦VOTE:promote⟧` activates differently based on context:

**Admin context** (high trust):

- Weight: 2.0
- Effect: Immediate
- Validation: None required

**New user context** (low trust):

- Weight: 0.5
- Effect: Deferred pending verification
- Validation: Required

**Blocked user context**:

- Weight: 0.0
- Effect: None (remains dormant)
- Validation: N/A

Identical notation; entirely different outcomes based on contextual gate evaluation.

---

## Symbol Notation & Types

### Notation Convention

`⟦TYPE:parameter⟧` - Makes dormant meaning visible and portable

### Symbol Classes

**Gates**: Filters determining activation permission

- Evaluate to boolean (may activate / must not activate)
- Must be evaluated before Events can execute

**Events**: Actions executing upon activation

- Only run after all relevant Gates pass
- Carry the actual semantic payload

### Symbol Lifecycle

At the level of concrete instances, symbols follow a lifecycle:

```text
Definition → Latent → [Gate Evaluation] → Activated → Bound → Archived
                                       ↘ Failed → Expired
```

- **Definition**: A symbolic contract template (how to interpret, what to do).
- **Latent**: A concrete "ticket" that may or may not bind under a future context.
- **Bound**: The ticket has successfully activated under a specific context.
- **Archived**: The ticket is no longer eligible for binding (its semantic potential is spent).
- **Failed / Expired**: The ticket could not bind (felicity conditions violated, or context moved on).

bindlang explicitly models this lifecycle so that systems can track not only what happened, but also what _could have happened but never did_.

---

## Symbol Consumption & Double-Spend Semantics

Deferred semantic binding introduces an additional concern beyond traditional speech-act theory: what prevents the same latent contract from being applied multiple times in ways that are semantically nonsensical?

In bindlang, each latent symbol is treated as a **binding ticket**: a single, portable opportunity to realize a specific performative effect under suitable context.

### One-Shot vs. Reusable Meaning

There are two distinct patterns of use:

- **One-shot tickets**
  Some performatives are inherently single-use:

  - `⟦MARRY:couple⟧`
  - `⟦APPROVE:invoice⟧`
  - `⟦SIGN:contract⟧`

  Once the contract has been successfully bound and its effect applied, it no longer makes sense to "spend" the exact same ticket again. The symbol's semantic potential has been **consumed**.

- **Reusable rules**
  Other patterns are naturally repeatable:

  - "When `temp > 30°C`, turn on the fan"
  - "When `submissions_open=true`, notify reviewers"
  - "When `has_weapon=true`, allow `attack`"

  Here the _pattern_ is stable, but each activation is a new event instance. The underlying rule may remain available for future contexts.

bindlang separates these concerns at the semantic level by distinguishing between:

- **Symbol definitions**: reusable templates ("how to interpret and what to do")
- **Symbol instances**: concrete tickets participating in the lifecycle above

### Default: Avoiding Double-Spend of Meaning

By default, bindlang treats each latent symbol instance as **one-shot**:

- Once a latent symbol binds and transitions to **Bound → Archived**, that particular ticket cannot bind again.
- This mirrors practices such as:

  - not counting the same ballot twice,
  - not applying the same signature to the same document twice,
  - not re-running the exact same approval step without minting a new approval opportunity.

This default prevents **double-spend of meaning**: a single semantic commitment cannot be implicitly reused multiple times without the system explicitly minting new tickets.

### Reusable Contracts

For domains that behave more like rule engines (e.g. monitoring, control systems, recurring workflows), bindlang allows symbol definitions to be interpreted as **reusable contracts**:

- The _definition_ remains latent across contexts.
- Each time the gate conditions are satisfied, a new **BoundSymbol event** is produced.
- State gates can be used to avoid pathological oscillations (e.g. only bind if `fan_on == false`).

- One-shot symbols model **unique performative events**.
- Reusable symbols model **standing rules** that can fire multiple times.

Systems must be explicit about whether latent meaning is a consumable ticket or a reusable rule.

---

## Foundation Symbol Library

The framework extends speech-act theory from Austin and Searle: tokens function as computational performatives whose illocutionary force is not fixed but varies with context. bindlang operationalizes this by making illocution a runtime computation over identity, timing, and system state.

### Core Symbols (Illustrative)

| Symbol             | Description                                    | Context Sensitivity  |
| ------------------ | ---------------------------------------------- | -------------------- |
| `⟦VOTE:promote⟧`   | Promotional voting with adaptive semantics     | Who, When, State     |
| `⟦WITNESS⟧`        | Multi-actor attestation with quorum            | Who (count), When    |
| `⟦GATE:sec_clean⟧` | Security gating with context-dependent cleanup | Who, State           |
| `⟦TRUST:target⟧`   | Trust assessment and scoring                   | Who (both), When     |
| `⟦CASCADE:viral⟧`  | Viral information propagation                  | Who (multiple), When |
| `⟦DECAY⟧`          | Temporal decay and state fading                | When, State          |

---

## Key Differentiators

### What bindlang Is NOT:

- **Not lazy evaluation**: Delays _what_, not _when_
- **Not promises**: No temporal deferral, semantic deferral
- **Not conditional logic**: Contracts travel with symbols, not scattered in if-statements
- **Not RAG/chunking**: Structured activation, not similarity search
- **Not summarization**: No lossy compression, full semantic preservation in latent form

### What bindlang IS:

- **Portable semantic contracts**: Symbol meaning defined once, evaluated anywhere
- **Context-aware activation**: Same symbol behaves differently in different contexts
- **Dependency-aware**: Cascade effects when state changes
- **Auditable**: Track what activated, what stayed dormant, and why
- **Compression through deferral**: Store latent, bind on-demand

---

## Design Principles

1. **Minimal core**: Prove fundamental concepts before expanding
2. **Type safety**: Strong typing for all semantic constructs
3. **Portability**: Symbols serialize cleanly to JSON
4. **Auditability**: Track what activated, what stayed latent, and why
5. **Domain-agnostic**: Applications span narrative, multi-agent, workflows, and authorization

---

## References & Prior Art

- **Theoretical foundation**: Latent/Bound semantics - [https://dsbl.dev/latentbound.html](https://dsbl.dev/latentbound.html)
- **Speech-act theory**: Austin, Searle (computational performatives)
- **Related work**:

  - Promises (temporal deferral) - different from semantic deferral
  - Lazy evaluation (computational efficiency) - bindlang is about semantic clarity
  - Modal logic (possible worlds) - bindlang makes context computationally explicit

---
