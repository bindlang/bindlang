# Audit Trail

[Back to Reference](index.md)

Complete reference for debugging with audit trail.

---

## BindingAttempt Structure

Every binding attempt (success or failure) creates a `BindingAttempt` record.

```python
from bindlang import BindingEngine, LatentSymbol, GateCondition, Context
from datetime import datetime

engine = BindingEngine()

# Register and bind
symbol = LatentSymbol(id="test", symbol_type="TEST:example", gate=GateCondition(who={"admin"}), payload={})
engine.register(symbol)

context = Context(who="user", when=datetime.now(), where="zone", state={})
result = engine.bind(symbol, context)

# Inspect audit trail
attempt = engine.audit.trail[0]
print(attempt)
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `symbol_id` | `str` | ID of the symbol that was attempted |
| `attempt_timestamp` | `datetime` | When the binding was attempted |
| `context_snapshot` | `Dict[str, Any]` | Context state at time of attempt |
| `success` | `bool` | True if binding succeeded, False if failed |
| `bound_symbol_id` | `Optional[str]` | Reference to BoundSymbol (only set on success) |
| `failure_reasons` | `List[FailureReason]` | Structured failure explanations (only on failure) |

### JSON Serialization

```python
attempt_dict = attempt.model_dump()
# {
#     'symbol_id': 'test',
#     'attempt_timestamp': '2024-11-16T12:00:00',
#     'context_snapshot': {'who': 'user', 'when': '...', 'where': 'zone', 'state': {}},
#     'success': False,
#     'bound_symbol_id': None,
#     'failure_reasons': [...]
# }
```

**Visual reference:** [Audit Trail diagram](../diagrams/core-architecture.md#audit-trail---tracking-binding-attempts) shows the complete audit architecture including BindingAttempt, FailureReason, and AuditSink system.

---

## FailureReason Structure

Structured explanation of why a gate condition failed.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `condition_type` | `str` | Which dimension failed: `who`, `when`, `where`, `state`, `dependency`, `expired` |
| `expected` | `Any` | What the gate required |
| `actual` | `Any` | What the context provided |
| `message` | `str` | Human-readable explanation |

### Example

```python
from bindlang import BindingEngine, LatentSymbol, GateCondition, Context
from datetime import datetime

engine = BindingEngine()

symbol = LatentSymbol(
    id="admin_action",
    symbol_type="ACTION:admin",
    gate=GateCondition(who={"admin", "moderator"}, state={"verified": True}),
    payload={}
)
engine.register(symbol)

context = Context(who="alice", when=datetime.now(), where="zone", state={"verified": False})
result = engine.bind(symbol, context)

# Inspect failure reasons
attempt = engine.audit.failed("admin_action")[0]
for reason in attempt.failure_reasons:
    print(f"{reason.condition_type}: {reason.message}")
# Output:
# who: 'alice' not in ['admin', 'moderator']
# state: state['verified']: expected True, got False
```

---

## Audit Manager API

Access via `engine.audit`.

### trail

Get all binding attempts (successes and failures).

```python
attempts = engine.audit.trail  # List[BindingAttempt]

for attempt in attempts:
    status = "SUCCESS" if attempt.success else "FAILED"
    print(f"{status}: {attempt.symbol_id} at {attempt.attempt_timestamp}")
```

---

### failed()

Get failed attempts for specific symbol.

```python
def failed(symbol_id: Optional[str] = None) -> List[BindingAttempt]
```

**Examples:**
```python
# All failures
all_failures = engine.audit.failed()

# Failures for specific symbol
symbol_failures = engine.audit.failed("vote_promote")

# Check if symbol ever failed
if engine.audit.failed("vote_promote"):
    print("Symbol has failures")
```

---

### explain()

Get human-readable explanation of why symbol failed.

```python
def explain(symbol_id: str) -> str
```

**Format:**
```
Symbol 'symbol_id' failed to activate:
  - who: 'actual_value' not in ['expected', 'values']
  - where: 'actual_value' not in ['expected', 'values']
  - when: temporal condition not met
  - state['key']: expected value, got actual_value
  - dependency: 'dep_id' not activated
```

**Example:**
```python
from bindlang import BindingEngine, LatentSymbol, GateCondition, Context
from datetime import datetime

engine = BindingEngine()

symbol = LatentSymbol(
    id="complex",
    symbol_type="ACTION:complex",
    gate=GateCondition(
        who={"admin"},
        where={"production"},
        state={"verified": True}
    ),
    payload={}
)
engine.register(symbol)

context = Context(
    who="alice",
    when=datetime.now(),
    where="development",
    state={"verified": False}
)
result = engine.bind(symbol, context)

print(engine.audit.explain("complex"))
# Output:
# Symbol 'complex' failed to activate:
#   - who: 'alice' not in ['admin']
#   - where: 'development' not in ['production']
#   - state['verified']: expected True, got False
```

**Returns:** Empty string if symbol never failed or doesn't exist.

---

### stats()

Get failure statistics by condition type.

```python
def stats() -> Dict[str, int]
```

**Example:**
```python
from bindlang import BindingEngine, LatentSymbol, GateCondition, Context
from datetime import datetime

engine = BindingEngine()

# Register multiple symbols with different gate conditions
symbols = [
    LatentSymbol(id="s1", symbol_type="T:s1", gate=GateCondition(who={"admin"}), payload={}),
    LatentSymbol(id="s2", symbol_type="T:s2", gate=GateCondition(who={"admin"}), payload={}),
    LatentSymbol(id="s3", symbol_type="T:s3", gate=GateCondition(where={"prod"}), payload={}),
    LatentSymbol(id="s4", symbol_type="T:s4", gate=GateCondition(state={"v": True}), payload={}, depends_on=["s5"]),
]

for sym in symbols:
    engine.register(sym)

context = Context(who="user", when=datetime.now(), where="dev", state={})
activated = engine.bind_all_registered(context)

stats = engine.audit.stats()
print(stats)
# Output: {'who': 2, 'where': 1, 'dependency': 1}
```

**Returns:** Dictionary mapping condition type to failure count.

---

## Filtering Attempts

Use list comprehensions to filter audit trail.

### By Success/Failure

```python
successes = [a for a in engine.audit.trail if a.success]
failures = [a for a in engine.audit.trail if not a.success]
```

### By Symbol Type

```python
vote_attempts = [a for a in engine.audit.trail if a.symbol_id.startswith("vote_")]
```

### By Time Range

```python
from datetime import datetime, timedelta

recent = datetime.now() - timedelta(hours=1)
recent_attempts = [a for a in engine.audit.trail if a.attempt_timestamp > recent]
```

### By Condition Type

```python
who_failures = [
    a for a in engine.audit.trail
    if not a.success and any(r.condition_type == "who" for r in a.failure_reasons)
]
```

---

## Identifying Latent Symbols

Symbols not in audit trail are **LATENT** (never attempted).

```python
all_ids = set(engine.symbol_registry.keys())
attempted_ids = {a.symbol_id for a in engine.audit.trail}
latent_ids = all_ids - attempted_ids

print(f"Latent symbols: {latent_ids}")
```

**Why symbols remain latent:**
- Dependencies not satisfied (required symbols not in `activated_symbols`)
- Future temporal conditions (e.g., `when="after:2099-01-01"` when context is 2024)
- State conditions not satisfied (e.g., `gate.state: {has_key: true}` when `context.state.has_key=false`)
- Who conditions not satisfied (e.g., `gate.who={"admin"}` when `context.who="user"`)
- Where conditions not satisfied (e.g., `gate.where={"production"}` when `context.where="dev"`)

Latent symbols are **not failures** — they are waiting for preconditions.

**Note on state-driven cascades:**
With reactive state mutations (default), symbols can become eligible mid-cascade:
```python
# Round 1: pick_up_key binds, sets has_key=True
# Round 2: unlock_door becomes eligible (state condition now satisfied)
bound, final_ctx = engine.bind_all_registered(context)
```

---

## Debugging Patterns

### Pattern 1: Find Why Symbol Never Activates

```python
symbol_id = "problematic_symbol"

if symbol_id not in engine.activated_symbols:
    explanation = engine.audit.explain(symbol_id)
    if explanation:
        print(f"Symbol failed:\n{explanation}")
    else:
        print("Symbol was never attempted (check if registered)")
```

### Pattern 2: Identify Common Failure Types

```python
stats = engine.audit.stats()
most_common = max(stats.items(), key=lambda x: x[1])
print(f"Most common failure: {most_common[0]} ({most_common[1]} times)")
```

### Pattern 3: Trace Dependency Chain Failure

```python
def trace_dependency_failure(engine, symbol_id):
    """Find root cause in dependency chain."""
    attempt = engine.audit.failed(symbol_id)
    if not attempt:
        return f"{symbol_id} never failed"

    for reason in attempt[0].failure_reasons:
        if reason.condition_type == "dependency":
            dep_id = reason.expected  # Dependency ID
            print(f"{symbol_id} failed because {dep_id} didn't activate")
            # Recurse to find why dependency failed
            trace_dependency_failure(engine, dep_id)
        else:
            print(f"{symbol_id} failed: {reason.message}")

trace_dependency_failure(engine, "final_step")
```

### Pattern 4: Compare Contexts Across Attempts

```python
symbol_id = "unstable_symbol"
attempts = [a for a in engine.audit.trail if a.symbol_id == symbol_id]

print(f"Symbol '{symbol_id}' attempted {len(attempts)} times")
for i, attempt in enumerate(attempts, 1):
    ctx = attempt.context_snapshot
    status = "SUCCESS" if attempt.success else "FAILED"
    print(f"  Attempt {i} [{status}]: who={ctx['who']}, where={ctx['where']}")
```

---

## Export for Analysis

Export audit trail for external analysis.

```python
# Export to JSON
engine.export.trail("audit.json")

# Export to JSONL (line-delimited)
engine.export.trail("audit.jsonl", fmt="jsonl")

# Export only failures
engine.export.failures("failures.json")
```

See [Serialization](serialization.md) for export details.

---

## Next Steps

- [BindingEngine](engine.md) - Main engine API
- [Debugging](debugging.md) - Additional debugging techniques
- [Common Patterns](patterns.md) - See dependency patterns in action
