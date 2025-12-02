# BindingEngine

[Back to Reference](index.md)

Orchestrates symbol registration and binding. The main runtime component.

---

## Constructor

```python
from bindlang import BindingEngine
from bindlang.core.sinks import JSONLFileSink, JSONFileSink

# Normal mode (in-memory only)
engine = BindingEngine()

# With JSONL sink
sink = JSONLFileSink("audit.jsonl", buffer_size=10)
engine = BindingEngine(audit_sink=sink)

# With JSON sink
sink = JSONFileSink("audit.json")
engine = BindingEngine(audit_sink=sink)

# With event hook
def on_activate(symbol, context, bound_symbol):
    print(f"Symbol {symbol.id} activated!")

engine = BindingEngine(on_symbol_activated=on_activate)

# Context manager (auto-close sink)
with BindingEngine(audit_sink=JSONLFileSink("audit.jsonl")) as engine:
    # operations...
    pass  # Auto-closes sink
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `audit_sink` | `Optional[AuditSink]` | `None` | Pluggable sink for audit trail storage |
| `on_symbol_activated` | `Optional[Callable]` | `None` | Callback when symbol activates |

See [examples/custom_sinks/](../../examples/custom_sinks/) for custom sink implementations.

---

## Core Methods

### register()

Register a latent symbol with the engine.

```python
def register(symbol: LatentSymbol) -> None
```

**Example:**
```python
engine.register(symbol)
```

**Raises:** `CircularDependencyError` if symbol creates dependency cycle

---

### bind()

Attempt to bind single symbol against context.

```python
def bind(symbol: LatentSymbol, context: Context) -> Optional[BoundSymbol]
```

**Example:**
```python
bound = engine.bind(symbol, context)
if bound:
    print(f"Success: {bound.effect}")
else:
    print(engine.audit.explain(symbol.id))
```

**Returns:** `BoundSymbol` if successful, `None` if conditions not met

**Side effects:**
- Records attempt in `engine.audit.trail`
- Updates `activated_symbols` set on success
- Fires `on_symbol_activated` callback on success

**Note:** Unlike `bind_all_registered()`, this method always attempts binding and records the result. Failed gate checks produce audit entries with `success=False`. Use this for explicit "try now" semantics. Use `bind_all_registered()` when symbols should remain LATENT until preconditions are met.

---

### bind_all()

Bind multiple symbols sequentially in provided order.

```python
def bind_all(symbol_ids: List[str], context: Context) -> List[BoundSymbol]
```

**Example:**
```python
bound = engine.bind_all(["symbol_1", "symbol_2", "symbol_3"], context)
print(f"Bound {len(bound)} symbols")
```

**Note:** Does not handle complex dependency ordering, just binds in sequence.

---

### bind_all_registered()

Bind all registered symbols with dependency cascade and reactive state mutations.

```python
def bind_all_registered(
    context: Context,
    max_iterations: int = 10,
    apply_state_mutations: bool = True
) -> Tuple[List[BoundSymbol], Context]
```

**Example:**
```python
# Default: reactive state mutations
bound, final_ctx = engine.bind_all_registered(context)
print(f"Activated {len(bound)} symbols")
print(f"Final state: {final_ctx.state}")

# Analytical mode: mutations recorded but not applied
bound, _ = engine.bind_all_registered(context, apply_state_mutations=False)
```

**Multi-round:** Iterates up to `max_iterations` rounds. Stops early if no progress is made (deadlock or no more eligible symbols). Productive dependency chains complete naturally - `max_iterations` protects against oscillation and deadlocks, not legitimate cascades

**Consumption Mode:**
- **`one_shot`** symbols (default): Archive after binding, removed from future rounds
- **`reusable`** symbols: Remain available for re-evaluation in subsequent rounds
- Each binding creates new BoundSymbol event regardless of consumption mode

**Pre-checks:** Only attempts symbols whose preconditions are met:
- Dependencies satisfied (all deps in `activated_symbols`)
- Temporal conditions allow binding (no future-only gates)
- State conditions satisfied (gate.state matches context.state)
- Who conditions satisfied (gate.who matches context.who or gate.who is None)
- Where conditions satisfied (gate.where matches context.where or gate.where is None)

Symbols failing preconditions remain **LATENT** (never attempted, no audit entry).

**Reactive State Mutations (default):**
- State mutations applied between rounds enable state-driven cascades
- Example: `pick_up_key → has_key=true → unlock_door`
- Context is immutable; mutations create new Context instances

**Conflict resolution:** Last-write-wins within same round.

**Analytical Mode:** Set `apply_state_mutations=False` to record mutations without applying them.

See [State Mutations Guide](../guides/state-mutations.md) for conflict behavior and detailed examples.

**Visual reference:** [Binding Process diagram](../diagrams/core-architecture.md#binding-process---detailed-flow) shows the complete flow including dependency checks and gate evaluation. [Dependency System diagram](../diagrams/core-architecture.md#dependency-system---cascade-activation) illustrates cascade activation across multiple rounds.

**Returns:**
- `Tuple[List[BoundSymbol], Context]`
  - `bound_symbols`: List of successfully bound symbols (with `state_changes_applied` if mutations enabled)
  - `final_context`: Context after all state mutations (same as input if `apply_state_mutations=False`)

See [Audit Trail](audit-trail.md#identifying-latent-symbols) for identifying latent symbols.

---

### bind_with_state_evolution()

Bind repeatedly with state updates between rounds.

```python
def bind_with_state_evolution(
    ctx: Context,
    max_rounds: int = 10,
    on_round_complete: Optional[Callable] = None
) -> Tuple[Context, int]
```

**Example:**
```python
def count_witnesses(engine, ctx, round_num):
    count = sum(1 for s in engine.activated_symbols if "witness" in s)
    return ctx.with_state_update("witness_count", count)

final_ctx, rounds = engine.bind_with_state_evolution(
    context,
    on_round_complete=count_witnesses
)
print(f"Converged in {rounds} rounds")
```

**Returns:** `(final_context, rounds_executed)`

---

## Manager-Based APIs

BindingEngine uses composition-based managers for specialized functionality.

### Audit Manager (`engine.audit`)

**Access audit trail:**
```python
# Get audit trail
attempts = engine.audit.trail

# Get failed attempts
failures = engine.audit.failed("vote_promote")

# Explain why symbol didn't activate
explanation = engine.audit.explain("vote_promote")
print(explanation)
# Output:
# Symbol 'vote_promote' failed to activate:
#   - who: 'alice' not in ['admin', 'moderator']

# Get failure statistics
stats = engine.audit.stats()
print(stats)  # {"who": 15, "dependency": 42, "state": 8}
```

See [Debugging](debugging.md) for detailed audit trail usage.

---

### Export Manager (`engine.export`)

**Export to files:**
```python
# Export full audit trail
engine.export.trail("audit.json")
engine.export.trail("audit.jsonl", fmt="jsonl")

# Export only failures
count = engine.export.failures("failures.json")
print(f"Exported {count} failures")

# Export state ledger
engine.export.ledger("ledger.json")
```

See [Serialization](serialization.md) for export details.

---

### Template Manager (`engine.templates`)

**Work with templates:**
```python
from bindlang.core.templates import SymbolTemplate

# Register template
template = SymbolTemplate(
    symbol_type_pattern="WITNESS:*",
    required_payload_fields={"agent_id", "role", "target_id"}
)
engine.templates.register(template)

# Create symbol from template
symbol = engine.templates.create(
    template_pattern="WITNESS:*",
    id="witness_1",
    symbol_type="WITNESS:attest",
    payload={"agent_id": "agent_1", "role": "witness", "target_id": "data_X"},
    gate=GateCondition(who={"agent_1"})
)
```

See [Templates](templates.md) for template details.

---

### Streaming Manager (`engine.streaming`)

**Streaming mode with sinks:**
```python
from bindlang.core.sinks import JSONLFileSink

# Context manager (auto-closes sink)
sink = JSONLFileSink("audit.jsonl", buffer_size=10)
with BindingEngine(audit_sink=sink) as engine:
    # Operations...
    pass  # Auto-flushes and closes sink

# Manual close
sink = JSONLFileSink("audit.jsonl")
engine = BindingEngine(audit_sink=sink)
# ... operations ...
engine.streaming.close()  # Flush and close sink

# Manual flush (force write buffered data)
engine.streaming.flush()
```

See [examples/custom_sinks/](../../examples/custom_sinks/) for custom sink implementations (SQLite, in-memory, multiplex).

---

## Next Steps

- [Templates](templates.md) - Learn about symbol templates
- [Debugging](debugging.md) - Use audit trail effectively
- [Common Patterns](patterns.md) - See engine in action
