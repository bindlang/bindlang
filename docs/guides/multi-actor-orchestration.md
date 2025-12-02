# Multi-Actor Orchestration Example

Complete example demonstrating multi-actor coordination with ActorSequenceRunner.

---

## Core Principle

**Context represents ONE actor's perspective (witness/speaker) at ONE moment in time.**

```python
Context(
    who="researcher_a",     # ONE actor (the witness)
    where="lab",            # ONE location
    when=datetime.now(),    # ONE moment
    state={...}             # World state (factual)
)
```

Multi-actor coordination is achieved through:
1. **State tracking** - `state` carries factual information about actor presence/actions
2. **Actor sequencing** - Multiple contexts executed in sequence with state carried forward

---

## Semantic Distinction: `who` vs `state`

### `who` gate - Actor ownership and accountability

Represents the **speaker/performer** of the action:
- Speech act theory: Who performs this performative utterance?
- Accountability: Who is responsible for this action?
- Witness: From whose perspective is this evaluated?

```python
{
    "id": "researcher_a_signs_document",
    "gate": {
        "who": ["researcher_a"],  # Only researcher_a can perform this
        ...
    }
}
```

### `state` gate - Factual prerequisites

Represents **factual conditions** in the world:
- Presence tracking: `researcher_a_present: true`
- Event completion: `experiment_complete: true`
- World conditions: `door_locked: false`

```python
{
    "id": "start_collaboration",
    "gate": {
        "who": null,  # System/omniscient perspective
        "state": {
            "researcher_a_present": true,  # Fact: A is present
            "researcher_b_present": true   # Fact: B is present
        }
    }
}
```

---

## Using ActorSequenceRunner

### Basic Usage

```python
from bindlang import BindingEngine, ActorSequenceRunner, LatentSymbol, GateCondition

# Create engine and register symbols
engine = BindingEngine()

# Symbol 1: Lab opens (system event, no specific actor)
lab_opens = LatentSymbol(
    id="lab_opens",
    symbol_type="EVENT:open",
    gate=GateCondition(who=None, where="lab_entrance"),
    payload={
        "action": "Lab opens",
        "state_mutation": {"lab_open": True}
    }
)
engine.register(lab_opens)

# Symbol 2: Researcher A arrives (A-specific action)
a_arrives = LatentSymbol(
    id="researcher_a_arrives",
    symbol_type="ACTION:arrive",
    gate=GateCondition(
        who={"researcher_a"},
        state={"lab_open": True}  # Requires lab to be open (fact)
    ),
    payload={
        "action": "Researcher A arrives",
        "state_mutation": {"researcher_a_present": True}
    }
)
engine.register(a_arrives)

# Symbol 3: Researcher B arrives (B-specific action)
b_arrives = LatentSymbol(
    id="researcher_b_arrives",
    symbol_type="ACTION:arrive",
    gate=GateCondition(
        who={"researcher_b"},
        state={"lab_open": True}
    ),
    payload={
        "action": "Researcher B arrives",
        "state_mutation": {"researcher_b_present": True}
    }
)
engine.register(b_arrives)

# Symbol 4: Collaboration starts (system event, requires both present)
collaboration = LatentSymbol(
    id="start_collaboration",
    symbol_type="EVENT:collaboration",
    gate=GateCondition(
        who=None,  # System perspective
        state={
            "researcher_a_present": True,
            "researcher_b_present": True
        }
    ),
    payload={"action": "Collaboration begins"}
)
engine.register(collaboration)

# Execute multi-actor sequence
runner = ActorSequenceRunner(engine)

actor_contexts = [
    {"who": None, "where": "lab_entrance"},           # System: lab opens
    {"who": "researcher_a", "where": "lab_entrance"}, # A arrives
    {"who": "researcher_b", "where": "lab_entrance"}, # B arrives
    {"who": None, "where": "main_lab"},               # System: collaboration
]

bound_symbols, final_state = runner.run_actor_sequence(
    actor_contexts,
    initial_state={"lab_open": False, "researcher_a_present": False, "researcher_b_present": False}
)

print(f"Bound {len(bound_symbols)} symbols")
print(f"Final state: {final_state}")
```

**Expected Output:**
```
Bound 4 symbols
Final state: {
    'lab_open': True,
    'researcher_a_present': True,
    'researcher_b_present': True
}
```

---

## Design Patterns

### Pattern 1: System Events

Use `who=None` for events that aren't owned by a specific actor:

```
lab_opens:         gate.who = null, gate.where = {lab_entrance}, payload.state_mutation = {lab_open: true}
experiment_starts: gate.who = null, gate.state = {all_researchers_ready: true}
```

### Pattern 2: Personal Actions

Use specific `who` for actions owned by an actor:

```
alice_signs: gate.who = {alice}, payload.state_mutation = {document_signed_by_alice: true}
```

### Pattern 3: Collaborative Prerequisites

Use `state` to track who has performed their part:

```
# Alice's part
alice_prepares: gate.who = {alice}, payload.state_mutation = {sample_prepared: true}

# Bob's part
bob_calibrates: gate.who = {bob}, payload.state_mutation = {equipment_calibrated: true}

# Collaborative action (system perspective)
run_experiment: gate.who = null, gate.state = {sample_prepared: true, equipment_calibrated: true}
```

### Pattern 4: Temporal Sequences

Use `run_with_timeline()` for time-based progression:

```python
from datetime import datetime, timedelta

base_time = datetime(2025, 11, 19, 9, 0)

timeline = [
    (base_time, None, "lab"),                                    # 09:00: Lab opens
    (base_time + timedelta(minutes=5), "alice", "lab"),          # 09:05: Alice arrives
    (base_time + timedelta(minutes=10), "bob", "lab"),           # 09:10: Bob arrives
    (base_time + timedelta(hours=1), None, "lab"),               # 10:00: Experiment starts
]

bound, state = runner.run_with_timeline(timeline, initial_state={})
```

---

## Common Mistakes

### Mistake: `who` for presence tracking

```
# INCORRECT: who={alice, bob} means "alice OR bob can perform"
collaboration: gate.who = {alice, bob}
```

Use state for presence, who for actor identity:

```
# CORRECT: Track presence in state
collaboration: gate.who = null, gate.state = {alice_present: true, bob_present: true}
```

### Mistake: Single context with multiple actors

```python
# INCORRECT: Multiple actors in one context
context = Context(who="alice_and_bob", ...)  # Violates witness semantics
```

Use actor sequence instead:

```python
# CORRECT: Multiple contexts
contexts = [
    {"who": "alice", "where": "lab"},
    {"who": "bob", "where": "lab"}
]
runner.run_actor_sequence(contexts)
```

---

## Theoretical Foundation

This design is grounded in:

1. **Speech Act Theory**
   - Each binding is a performative utterance
   - `who` identifies the speaker/performer
   - Audit trail tracks "who said/did what"

2. **Proof-of-Witness**
   - Context is a witness perspective
   - One witness per binding evaluation
   - Multi-witness scenarios = multiple evaluations

3. **Reactive State Mutations**
   - State carries forward between perspectives
   - Actor A's actions become facts for Actor B's evaluation
   - Enables coordination without breaking witness semantics

4. **Latent/Bound Semantics**
   - Symbols remain latent until their specific actor's perspective arrives
   - `who` gate pre-check prevents inappropriate binding attempts
   - Clear distinction: latent (waiting) vs failed (attempted but denied)

---

## Key Concepts

| Concept | Meaning |
|---------|---------|
| Context | ONE actor's perspective (witness) |
| `who` | Speaker/performer of action |
| `state` | Factual world conditions (including actor presence) |
| ActorSequenceRunner | Orchestration pattern for multi-actor sequences |
| State mutations | Carry between actor perspectives |
