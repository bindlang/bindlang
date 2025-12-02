# Core Models

[Back to Reference](index.md)

---

## LatentSymbol

Dormant meaning awaiting context. The fundamental unit of bindlang.

```python
from bindlang import LatentSymbol, GateCondition

symbol = LatentSymbol(
    id="char_anna_brave",
    symbol_type="CHARSTATE:brave",
    gate=GateCondition(where={"beach"}),
    payload={"character": "Anna", "emotion": "brave"},
    metadata={"author": "system", "version": "1.0"},
    depends_on=["char_anna_arrives"],
    consumption="one_shot"
)
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | `str` | Yes | Unique identifier for the symbol |
| `symbol_type` | `str` | Yes | Type in format `CATEGORY:name` (e.g., `VOTE:promote`) |
| `gate` | `GateCondition` | Yes | Conditions for activation |
| `payload` | `Dict[str, Any]` | No | Data carried by symbol (default: `{}`) |
| `metadata` | `Dict[str, Any]` | No | Additional metadata (default: `{}`) |
| `depends_on` | `List[str]` | No | IDs of symbols that must activate first (default: `[]`) |
| `consumption` | `str` | No | Consumption mode: `"one_shot"` (default) or `"reusable"` |

### Consumption Modes

**`"one_shot"`** (default):
- Symbol archives after binding (Latent → Bound → Archived)
- Prevents double-spend of meaning
- Use for unique events: narratives, workflows, approvals

**`"reusable"`**:
- Symbol remains latent after binding (Latent ⇄ Bound)
- Can bind multiple times, each creating new BoundSymbol event
- Use for rule engines: monitoring, reactive systems, iterations

See [FOUNDATION.md](../theory/FOUNDATION.md#symbol-consumption--double-spend-semantics) for theoretical background.

### Properties

- **Immutable:** Yes (Pydantic frozen model)
- **Serializable:** Yes (JSON round-trip via Pydantic)

### JSON Serialization

```python
# To JSON
json_str = symbol.model_dump_json()

# From JSON
from bindlang import LatentSymbol
symbol = LatentSymbol.model_validate_json(json_str)
```

---

## GateCondition

Four-dimensional filter determining when a symbol can bind.

```python
from bindlang import GateCondition

# Simple gate - single dimension
gate = GateCondition(who={"alice", "bob"})

# Multi-dimensional gate
gate = GateCondition(
    who={"admin", "moderator"},
    where={"production", "staging"},
    when="after:2024-01-01",
    state={"verified": True, "level": 5}
)

# Empty gate - always passes
gate = GateCondition()
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `who` | `Optional[Set[str]]` | No | Actor must be in this set |
| `where` | `Optional[Set[str]]` | No | Location must be in this set |
| `when` | `Optional[str]` | No | Temporal expression (see below) |
| `state` | `Optional[Dict[str, Any]]` | No | State keys must match exactly |

### Semantic Distinction: `who` vs `state`

**`who` gate** - Actor ownership and accountability
- Represents the **speaker/performer** of the action
- Defines who is responsible for this action
- Example: `GateCondition(who={"admin"})` - Only admin can perform this

**`state` gate** - Factual prerequisites
- Represents **factual conditions** in the world
- Presence tracking: `{"researcher_a_present": True}`
- Event completion: `{"experiment_complete": True}`
- Example: `GateCondition(state={"verified": True})` - User must be verified

**When to use which:**
- Use `who` for actions owned by specific actors
- Use `state` for tracking actor presence or world conditions
- Multi-actor scenarios: Track presence in `state`, specify performer with `who`

See [When to Use What](../guides/when-to-use-what.md) for complete decision guide.

**Visual reference:** [Gate System diagram](../diagrams/core-architecture.md#the-gate-system---context-matching) shows how all four dimensions (who/where/when/state) combine with AND logic.

### Temporal Expressions

```python
# Absolute datetime (ISO format)
GateCondition(when="after:2024-01-01T12:00:00")
GateCondition(when="before:2025-12-31T23:59:59")

# Symbolic state reference
GateCondition(when="after:user_verified")  # Checks context.state["user_verified"]
```

### Evaluation Rules

- All present conditions must pass (implicit AND)
- `None` conditions are ignored
- Empty gate (`GateCondition()`) always passes

### Properties

- **Immutable:** Yes

---

## Context

Runtime state for evaluating symbols. Immutable four-dimensional snapshot.

```python
from bindlang import Context
from datetime import datetime

context = Context(
    who="alice",
    when=datetime.now(),
    where="production",
    state={"verified": True, "level": 5}
)

# Update state (returns new Context instance)
new_context = context.with_state_update("witness_count", 3)
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `who` | `Optional[str]` | No | Actor/witness perspective (default: `None`) |
| `when` | `datetime` | Yes | Timestamp of binding attempt |
| `where` | `str` | Yes | Location/zone/environment |
| `state` | `Dict[str, Any]` | No | Arbitrary state dict (default: `{}`) |

**`who` Semantics:**
- **Specific actor:** `"researcher_a"`, `"alice"`, `"admin"` - Represents a specific actor's perspective
- **System/omniscient:** `None` - No specific actor; represents system-level events or omniscient perspective
- Used for determining who performs or owns the action

### Methods

#### with_state_update()

Return a new Context with an updated state key/value.

```python
def with_state_update(key: str, value: Any) -> Context
```

**Example:**
```python
ctx = Context(who="alice", when=now, where="zone", state={"count": 0})
new_ctx = ctx.with_state_update("count", 42)
# ctx.state["count"] == 0 (original unchanged)
# new_ctx.state["count"] == 42 (new instance)
```

### Properties

- **Immutable:** Yes

---

## BoundSymbol

Symbol that successfully activated. Contains effect and context snapshot.

**Note:** You don't construct BoundSymbol directly - it's created by `BindingEngine.bind()`

```python
bound = engine.bind(symbol, context)
if bound:
    print(f"Symbol ID: {bound.symbol_id}")
    print(f"Type: {bound.symbol_type}")
    print(f"Effect: {bound.effect}")
    print(f"Weight: {bound.weight}")
    print(f"Bound at: {bound.bound_at}")
    print(f"Context: {bound.context_snapshot}")
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `symbol_id` | `str` | ID of the original LatentSymbol |
| `symbol_type` | `str` | Type of the symbol |
| `effect` | `Dict[str, Any]` | Effect payload (from symbol.payload) |
| `weight` | `float` | Weight factor (default: 1.0) |
| `bound_at` | `datetime` | Timestamp of binding |
| `context_snapshot` | `Dict[str, Any]` | Context state at binding time |
| `state_changes_applied` | `Optional[List[Dict[str, Any]]]` | State mutations applied (only when `apply_state_mutations=True`) |

### Properties

- **Immutable:** Read-only (not enforced but intended)

---

## BindingAttempt

Record of a binding attempt. Created automatically by `BindingEngine.bind()`.

**Note:** You don't construct BindingAttempt directly - access via `engine.audit.trail`

```python
from bindlang import BindingEngine, LatentSymbol, GateCondition, Context
from datetime import datetime

engine = BindingEngine()

symbol = LatentSymbol(
    id="test",
    symbol_type="TEST:example",
    gate=GateCondition(who={"admin"}),
    payload={}
)
engine.register(symbol)

context = Context(who="user", when=datetime.now(), where="zone", state={})
result = engine.bind(symbol, context)

# Access attempt from audit trail
attempt = engine.audit.trail[0]
print(f"Success: {attempt.success}")
print(f"Symbol: {attempt.symbol_id}")
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `symbol_id` | `str` | ID of symbol that was attempted |
| `attempt_timestamp` | `datetime` | When the binding was attempted |
| `context_snapshot` | `Dict[str, Any]` | Context state at time of attempt |
| `success` | `bool` | True if binding succeeded, False if failed |
| `bound_symbol_id` | `Optional[str]` | Reference to BoundSymbol (only on success) |
| `failure_reasons` | `List[FailureReason]` | Why binding failed (only on failure) |

### JSON Serialization

```python
attempt_dict = attempt.model_dump()
# {
#     'symbol_id': 'test',
#     'attempt_timestamp': '2024-11-16T12:00:00',
#     'context_snapshot': {...},
#     'success': False,
#     'bound_symbol_id': None,
#     'failure_reasons': [...]
# }

# To JSON string
json_str = attempt.model_dump_json()
```

### Properties

- **Immutable:** Yes (Pydantic frozen model)
- **Serializable:** Yes (JSON round-trip via Pydantic)

---

## FailureReason

Structured explanation of why a gate condition failed. Part of BindingAttempt.

```python
from bindlang import BindingEngine, LatentSymbol, GateCondition, Context
from datetime import datetime

engine = BindingEngine()

symbol = LatentSymbol(
    id="admin_only",
    symbol_type="ACTION:admin",
    gate=GateCondition(who={"admin"}),
    payload={}
)
engine.register(symbol)

context = Context(who="alice", when=datetime.now(), where="zone", state={})
result = engine.bind(symbol, context)

# Access failure reasons
attempt = engine.audit.trail[0]
for reason in attempt.failure_reasons:
    print(f"{reason.condition_type}: {reason.message}")
# Output: who: 'alice' not in ['admin']
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `condition_type` | `str` | Which dimension failed: `who`, `when`, `where`, `state`, `dependency`, `expired` |
| `expected` | `Any` | What the gate required |
| `actual` | `Any` | What the context provided |
| `message` | `str` | Human-readable explanation |

### Condition Types

| Type | Description | Example Message |
|------|-------------|-----------------|
| `who` | Actor not in allowed set | `'alice' not in ['admin']` |
| `where` | Location not in allowed set | `'dev' not in ['production']` |
| `when` | Temporal condition failed | `temporal condition not met` |
| `state` | State value mismatch | `state['verified']: expected True, got False` |
| `dependency` | Required symbol not activated | `dependency: 'symbol_a' not activated` |
| `expired` | Symbol past expiration | `symbol expired` |

### Properties

- **Immutable:** Yes (Pydantic frozen model)
- **Serializable:** Yes (JSON round-trip via Pydantic)

---

## Next Steps

- [BindingEngine](engine.md) - Learn how to bind symbols
- [Audit Trail](audit-trail.md) - Debug with BindingAttempt
- [Quick Start](quickstart.md) - See models in action
- [Common Patterns](patterns.md) - Practical examples
