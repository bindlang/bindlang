# Orchestration

[Back to Reference](index.md)

Multi-actor execution orchestrator for binding across multiple actor perspectives.

---

## ActorSequenceRunner

Executes binding from multiple actor perspectives in sequence, carrying state mutations between contexts.

**Core Principle:** Context represents ONE actor's perspective (witness/speaker) at ONE moment in time.

```python
from bindlang import BindingEngine, ActorSequenceRunner, LatentSymbol, GateCondition

# Setup engine with symbols
engine = BindingEngine()

# System event (no specific actor)
lab_opens = LatentSymbol(
    id="lab_opens",
    symbol_type="EVENT:open",
    gate=GateCondition(who=None, where={"lab_entrance"}),
    payload={"state_mutation": {"lab_open": True}}
)
engine.register(lab_opens)

# Actor-specific action
a_arrives = LatentSymbol(
    id="researcher_a_arrives",
    symbol_type="ACTION:arrive",
    gate=GateCondition(
        who={"researcher_a"},
        state={"lab_open": True}
    ),
    payload={"state_mutation": {"researcher_a_present": True}}
)
engine.register(a_arrives)

# Execute multi-actor sequence
runner = ActorSequenceRunner(engine)

actor_contexts = [
    {"who": None, "where": "lab_entrance"},           # System: lab opens
    {"who": "researcher_a", "where": "lab_entrance"}, # A arrives
]

bound, final_state = runner.run_actor_sequence(
    actor_contexts,
    initial_state={"lab_open": False, "researcher_a_present": False}
)

print(f"Bound {len(bound)} symbols")
print(f"Final state: {final_state}")
```

**Visual reference:** [ActorSequenceRunner diagram](../diagrams/core-architecture.md#multi-actor-orchestration---actorsequencerunner) shows the sequential perspective flow with shared state mutations and witness semantics.

---

## Constructor

```python
def __init__(engine: BindingEngine)
```

Initialize with a BindingEngine instance containing registered symbols.

**Example:**
```python
from bindlang import BindingEngine, ActorSequenceRunner

engine = BindingEngine()
# ... register symbols ...

runner = ActorSequenceRunner(engine)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `engine` | `BindingEngine` | Yes | Engine with registered symbols |

---

## Core Methods

### run_actor_sequence()

Execute binding across multiple actor perspectives with state carried forward.

```python
def run_actor_sequence(
    actor_contexts: List[Dict[str, Any]],
    initial_state: Optional[Dict[str, Any]] = None,
    initial_when: Optional[datetime] = None,
) -> Tuple[List[BoundSymbol], Dict[str, Any]]
```

**Example:**
```python
from datetime import datetime

actor_contexts = [
    {"who": None, "where": "lobby"},
    {"who": "alice", "where": "lobby"},
    {"who": "bob", "where": "lobby"},
]

bound, final_state = runner.run_actor_sequence(
    actor_contexts,
    initial_state={"door_open": False}
)

print(f"Activated {len(bound)} symbols")
print(f"Final state: {final_state}")
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `actor_contexts` | `List[Dict[str, Any]]` | Yes | List of context templates (see below) |
| `initial_state` | `Optional[Dict[str, Any]]` | No | Initial world state (default: `{}`) |
| `initial_when` | `Optional[datetime]` | No | Initial timestamp (default: `datetime.now()`) |

**Context Template Structure:**

Each dict in `actor_contexts` should contain:

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `who` | `Optional[str]` | Yes | Actor identifier (None for system perspective) |
| `where` | `str` | No | Location (default: `""`) |
| `when` | `datetime` | No | Timestamp (default: uses `initial_when`) |

**Returns:** `Tuple[List[BoundSymbol], Dict[str, Any]]`
- `bound_symbols`: All BoundSymbols from all perspectives (in order)
- `final_state`: State after all actor perspectives have executed

**Behavior:**
- Executes binding for each actor perspective in sequence
- State mutations from each perspective carry forward to next
- Enables reactive coordination: Actor A's actions become facts for Actor B
- Each perspective sees accumulated state from previous perspectives

**Within-perspective execution:**
- Each actor perspective runs `bind_all_registered()` internally
- State mutations apply **between rounds**, not within same round
- Multiple symbols checked in same round see the same initial context
- Use `depends_on` to enforce ordering if state checks must happen after mutations

---

### run_with_timeline()

Execute binding with explicit timeline of (when, who, where) tuples.

```python
def run_with_timeline(
    actor_timeline: List[Tuple[datetime, str, str]],
    initial_state: Optional[Dict[str, Any]] = None,
) -> Tuple[List[BoundSymbol], Dict[str, Any]]
```

**Example:**
```python
from datetime import datetime, timedelta

base_time = datetime(2025, 11, 19, 9, 0)

actor_timeline = [
    (base_time, None, "lab"),                                    # 09:00: Lab opens
    (base_time + timedelta(minutes=5), "researcher_a", "lab"),   # 09:05: A arrives
    (base_time + timedelta(minutes=10), "researcher_b", "lab"),  # 09:10: B arrives
]

bound, final_state = runner.run_with_timeline(
    actor_timeline,
    initial_state={"lab_open": False}
)

print(f"Timeline executed: {len(bound)} symbols bound")
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `actor_timeline` | `List[Tuple[datetime, str, str]]` | Yes | List of (when, who, where) tuples |
| `initial_state` | `Optional[Dict[str, Any]]` | No | Initial world state (default: `{}`) |

**Timeline Tuple Structure:** `(when, who, where)`
- `when`: `datetime` - Timestamp for this perspective
- `who`: `Optional[str]` - Actor identifier (None for system)
- `where`: `str` - Location

**Returns:** Same as `run_actor_sequence()`

**Use Cases:**
- Time-based progression scenarios
- Event timelines with specific timestamps
- Temporal ordering requirements

---

## Design Principles

### Witness Semantics

**Context = ONE actor's perspective at ONE moment:**
```python
Context(
    who="researcher_a",     # ONE actor (the witness)
    where="lab",            # ONE location
    when=datetime.now(),    # ONE moment
    state={...}             # World state (factual)
)
```

**Multi-actor coordination achieved through:**
1. **State tracking** - `state` carries factual information about actor presence/actions
2. **Actor sequencing** - Multiple contexts executed in sequence with state carried forward

### Semantic Distinction: `who` vs `state`

**`who` gate** - Actor ownership (who performs the action)
**`state` gate** - Factual prerequisites (world conditions)

See [Models](models.md#semantic-distinction-who-vs-state) for complete semantic distinction.

### Design Patterns

**Pattern 1: System Events**

Use `who=None` for events not owned by a specific actor:
```python
{
    "id": "lab_opens",
    "gate": {"who": None, "where": {"lab_entrance"}},
    "payload": {"state_mutation": {"lab_open": True}}
}
```

**Pattern 2: Personal Actions**

Use specific `who` for actions owned by an actor:
```python
{
    "id": "alice_signs_document",
    "gate": {"who": {"alice"}},
    "payload": {"state_mutation": {"document_signed_by_alice": True}}
}
```

**Pattern 3: Collaborative Prerequisites**

Use `state` to track who has performed their part:
```python
# Alice's part
{
    "id": "alice_prepares",
    "gate": {"who": {"alice"}},
    "payload": {"state_mutation": {"sample_prepared": True}}
}

# Bob's part
{
    "id": "bob_calibrates",
    "gate": {"who": {"bob"}},
    "payload": {"state_mutation": {"equipment_calibrated": True}}
}

# System checks both conditions
{
    "id": "run_experiment",
    "gate": {
        "who": None,
        "state": {
            "sample_prepared": True,
            "equipment_calibrated": True
        }
    }
}
```

---

## Examples

### Example 1: Lab Collaboration Workflow

Complete example showing system events, actor-specific actions, and state-driven coordination.

```python
from bindlang import BindingEngine, ActorSequenceRunner, LatentSymbol, GateCondition
from datetime import datetime

engine = BindingEngine()

# System event - no specific actor
lab_opens = LatentSymbol(
    id="lab_opens",
    symbol_type="EVENT:open",
    gate=GateCondition(who=None, where={"lab_entrance"}),
    payload={"state_mutation": {"lab_open": True}}
)
engine.register(lab_opens)

# Researcher A arrives - requires lab to be open (factual prerequisite)
a_arrives = LatentSymbol(
    id="researcher_a_arrives",
    symbol_type="ACTION:arrive",
    gate=GateCondition(
        who={"researcher_a"},
        state={"lab_open": True}  # Fact: lab must be open
    ),
    payload={"state_mutation": {"researcher_a_present": True}}
)
engine.register(a_arrives)

# Researcher B arrives - requires lab to be open
b_arrives = LatentSymbol(
    id="researcher_b_arrives",
    symbol_type="ACTION:arrive",
    gate=GateCondition(
        who={"researcher_b"},
        state={"lab_open": True}
    ),
    payload={"state_mutation": {"researcher_b_present": True}}
)
engine.register(b_arrives)

# Collaboration starts - system event requiring both present
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

bound, final_state = runner.run_actor_sequence(
    actor_contexts,
    initial_state={
        "lab_open": False,
        "researcher_a_present": False,
        "researcher_b_present": False
    }
)

print(f"Bound {len(bound)} symbols")
print(f"Final state: {final_state}")
# Output:
# Bound 4 symbols
# Final state: {'lab_open': True, 'researcher_a_present': True, 'researcher_b_present': True}
```

**Key Concepts:**
- **System events:** Use `who=None` for events not owned by specific actors
- **Actor actions:** Use specific `who` for actions owned by actors
- **State tracking:** Use `state` to track presence and world facts
- **Reactive coordination:** State mutations from one actor enable next actor's bindings

**When to use:**
- Multi-party workflows (approval chains, collaboration)
- Actor presence tracking (meetings, arrivals/departures)
- Sequential actions by different actors
- System events triggered by actor states

---

## Common Pitfalls

### Mistake: Using `who` for presence tracking

```python
# INCORRECT: Trying to track both actors in who
{
    "gate": {
        "who": {"alice", "bob"},  # This means "alice OR bob can perform"
    }
}
```

**Solution:** Use state for presence, who for actor identity

```python
# CORRECT: Track presence in state
{
    "id": "collaboration_starts",
    "gate": {
        "who": None,  # System event
        "state": {
            "alice_present": True,
            "bob_present": True
        }
    }
}
```

### Mistake: Single context with multiple actors

```python
# INCORRECT: Trying to represent multiple actors in one context
context = Context(who="alice_and_bob", ...)  # Violates witness semantics
```

**Solution:** Use actor sequence

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

## Next Steps

- [Models](models.md) - Understand Context and GateCondition semantics
- [BindingEngine](engine.md) - Learn about state mutations and pre-checks
- [Common Patterns](patterns.md) - See multi-actor patterns in action
- [Debugging](debugging.md) - Debug multi-actor scenarios
- [Multi-Actor Guide](../guides/multi-actor-orchestration.md) - Complete multi-actor workflow guide
