# Common Patterns

[Back to Reference](index.md)

Copy-paste solutions for typical single-actor use cases. For multi-actor coordination, see [Orchestration](orchestration.md).

---

## Pattern 1: Simple Authorization

Control who can perform actions.

```python
from bindlang import LatentSymbol, GateCondition, Context, BindingEngine
from datetime import datetime

# Setup
engine = BindingEngine()

# Admin action - only admins can promote
promote = LatentSymbol(
    id="promote_alice",
    symbol_type="ACTION:promote",
    gate=GateCondition(who={"admin"}),
    payload={"target": "alice", "new_role": "moderator"}
)
engine.register(promote)

# Context: regular user tries
user_ctx = Context(who="bob", when=datetime.now(), where="app", state={})
result = engine.bind(promote, user_ctx)
# result is None - bob is not admin

# Context: admin tries
admin_ctx = Context(who="admin", when=datetime.now(), where="app", state={})
result = engine.bind(promote, admin_ctx)
# result is BoundSymbol - admin succeeds
```

---

## Pattern 2: Dependency Chain

Symbol A must activate before B, B before C.

```python
from bindlang import LatentSymbol, GateCondition, BindingEngine, Context
from datetime import datetime

engine = BindingEngine()

# Step A
a = LatentSymbol(
    id="a", symbol_type="STEP:first",
    gate=GateCondition(who={"system"}),
    payload={"step": 1}
)

# Step B - depends on A
b = LatentSymbol(
    id="b", symbol_type="STEP:second",
    gate=GateCondition(who={"system"}),
    payload={"step": 2},
    depends_on=["a"]
)

# Step C - depends on B
c = LatentSymbol(
    id="c", symbol_type="STEP:third",
    gate=GateCondition(who={"system"}),
    payload={"step": 3},
    depends_on=["b"]
)

engine.register(a)
engine.register(b)
engine.register(c)

# Bind all - engine handles cascade automatically
context = Context(who="system", when=datetime.now(), where="zone", state={})
activated = engine.bind_all_registered(context)
# activated contains [a, b, c] in dependency order
```

---

## Pattern 3: Temporal Deadlines

Symbols that expire after a specific date.

```python
from bindlang import LatentSymbol, GateCondition, Context, BindingEngine
from datetime import datetime

engine = BindingEngine()

# Symbol expires after specific date
deadline_symbol = LatentSymbol(
    id="early_bird",
    symbol_type="DISCOUNT:early",
    gate=GateCondition(when="before:2024-12-31T23:59:59"),
    payload={"discount": 0.20}
)
engine.register(deadline_symbol)

# Activate before deadline
early_ctx = Context(
    who="customer",
    when=datetime(2024, 6, 1),
    where="shop",
    state={}
)
result = engine.bind(deadline_symbol, early_ctx)
# result is BoundSymbol - before deadline

# Try after deadline
late_ctx = Context(
    who="customer",
    when=datetime(2025, 1, 1),
    where="shop",
    state={}
)
result = engine.bind(deadline_symbol, late_ctx)
# result is None - deadline passed
```

---

## Pattern 4: State-Based Activation

Symbols requiring specific state conditions.

```python
from bindlang import LatentSymbol, GateCondition, Context, BindingEngine
from datetime import datetime

engine = BindingEngine()

# Symbol requires specific state conditions
verified_action = LatentSymbol(
    id="withdraw_funds",
    symbol_type="ACTION:withdraw",
    gate=GateCondition(
        who={"user"},
        state={"verified": True, "balance_positive": True}
    ),
    payload={"amount": 100}
)
engine.register(verified_action)

# Context without required state
unverified_ctx = Context(
    who="user",
    when=datetime.now(),
    where="app",
    state={"verified": False}
)
result = engine.bind(verified_action, unverified_ctx)
# result is None - not verified

# Context with required state
verified_ctx = Context(
    who="user",
    when=datetime.now(),
    where="app",
    state={"verified": True, "balance_positive": True}
)
result = engine.bind(verified_action, verified_ctx)
# result is BoundSymbol - conditions met
```

---

## Pattern 5: Multi-Agent Quorum

Track witness count and detect quorum emergence.

```python
from bindlang import LatentSymbol, GateCondition, Context, BindingEngine
from datetime import datetime

engine = BindingEngine()

# Track witness count with state evolution
def witness_counter(engine, ctx, round_num):
    count = sum(1 for s in engine.activated_symbols if s.startswith("witness_"))
    return ctx.with_state_update("witness_count", count)

# Create 5 witness symbols
for i in range(5):
    witness = LatentSymbol(
        id=f"witness_{i}",
        symbol_type="WITNESS:attest",
        gate=GateCondition(who={f"agent_{i}"}),
        payload={"agent_id": f"agent_{i}"}
    )
    engine.register(witness)

# Quorum symbol - needs 3 witnesses
quorum = LatentSymbol(
    id="quorum_reached",
    symbol_type="EVENT:quorum",
    gate=GateCondition(state={"witness_count": 3}),
    payload={"threshold_met": True}
)
engine.register(quorum)

# Simulate 3 agents witnessing
ctx = Context(who="agent_0", when=datetime.now(), where="zone", state={})
final_ctx, rounds = engine.bind_with_state_evolution(
    ctx,
    on_round_complete=witness_counter
)

# Check if quorum reached
if "quorum_reached" in engine.activated_symbols:
    print("Quorum achieved!")
```

**Visual reference:** [Multi-Agent Witness Quorum diagram](../diagrams/advanced-patterns.md#multi-agent-witness-quorum) shows how independent agent symbols compose into emergent quorum semantics.

---

## Pattern 6: Streaming Audit Trail

Auto-write binding attempts to disk for real-time monitoring.

```python
from bindlang import BindingEngine, LatentSymbol, Context
import json

# Auto-write binding attempts to disk
with BindingEngine(audit_file="live_audit.jsonl") as engine:
    # Register symbols
    for symbol in symbols:
        engine.register(symbol)

    # Bind - writes to file automatically
    activated = engine.bind_all_registered(context)

# File closed and flushed automatically

# Read back later:
with open("live_audit.jsonl") as f:
    for line in f:
        attempt = json.loads(line)
        print(f"Symbol: {attempt['symbol_id']}, Success: {attempt['success']}")
```

---

## Pattern 7: Event Hooks

React to symbol activations in real-time.

```python
from bindlang import BindingEngine, LatentSymbol, GateCondition, Context
from datetime import datetime

# Define activation callback
def log_activation(symbol, context, bound_symbol):
    print(f"[EVENT] {symbol.id} activated by {context.who} at {context.where}")
    print(f"[EFFECT] {bound_symbol.effect}")

# Create engine with hook
engine = BindingEngine(on_symbol_activated=log_activation)

# Register and bind - hook fires on each activation
symbol = LatentSymbol(
    id="vote_promote",
    symbol_type="VOTE:promote",
    gate=GateCondition(who={"admin"}),
    payload={"target": "alice", "weight": 1.0}
)
engine.register(symbol)

context = Context(who="admin", when=datetime.now(), where="production", state={})
result = engine.bind(symbol, context)

# Hook prints:
# [EVENT] vote_promote activated by admin at production
# [EFFECT] {'target': 'alice', 'weight': 1.0}
```

---

## Pattern 8: Reusable Rules for Reactive Systems

Symbols that can bind multiple times across rounds.

```python
from bindlang import LatentSymbol, GateCondition, Context, BindingEngine
from datetime import datetime

engine = BindingEngine()

# Reusable rule: activate when flag is false
activate = LatentSymbol(
    id="activate",
    symbol_type="RULE:activate",
    consumption="reusable",
    gate=GateCondition(state={"active": False}),
    payload={"state_mutation": {"active": True}}
)

# Reusable rule: deactivate when flag is true
deactivate = LatentSymbol(
    id="deactivate",
    symbol_type="RULE:deactivate",
    consumption="reusable",
    gate=GateCondition(state={"active": True}),
    payload={"state_mutation": {"active": False}}
)

engine.register(activate)
engine.register(deactivate)

# Bind with multiple rounds - rules trigger alternately
context = Context(who="system", when=datetime.now(), where="zone", state={"active": False})
bound, final_ctx = engine.bind_all_registered(context, max_iterations=6)

# Result: activate → deactivate → activate → deactivate → ... (6 bindings total)
# Each reusable symbol binds multiple times, creating new BoundSymbol events
```

**Use for:** Rule engines, monitoring systems, reactive workflows, iterative processes.

**Note:** Use `max_iterations` to prevent infinite loops. For complex oscillation scenarios, see `examples/`.

---

## Pattern 9: Fallback Chain

Try primary symbol, if latent try fallback.

```python
from bindlang import LatentSymbol, GateCondition, Context, BindingEngine, sym
from datetime import datetime

engine = BindingEngine()

# Primary action - admin only
primary = LatentSymbol(
    id="admin_action",
    symbol_type="ACTION:admin",
    gate=GateCondition(who={"admin"}),
    payload={"level": "full"}
)

# Fallback - any user
fallback = LatentSymbol(
    id="user_action",
    symbol_type="ACTION:user",
    gate=GateCondition(who={"user", "admin"}),
    payload={"level": "limited"}
)

engine.register(primary)
engine.register(fallback)

# Compose with | operator
resilient = sym(primary) | sym(fallback)

# User tries - falls back to limited action
user_ctx = Context(who="user", when=datetime.now(), where="app", state={})
result = resilient.try_bind(user_ctx, engine)
# result.bound.symbol_id == "user_action"

# Admin tries - gets full action
admin_ctx = Context(who="admin", when=datetime.now(), where="app", state={})
result = resilient.try_bind(admin_ctx, engine)
# result.bound.symbol_id == "admin_action"
```

Chain multiple fallbacks:

```python
resilient = sym(primary) | sym(secondary) | sym(tertiary)
```

Both attempts are logged to audit trail.

---

## Pattern 10: Sequential Gate

Left must bind before right is attempted.

```python
from bindlang import LatentSymbol, GateCondition, Context, BindingEngine, sym
from datetime import datetime

engine = BindingEngine()

# Gate must pass before action runs
gate = LatentSymbol(
    id="auth_gate",
    symbol_type="GATE:auth",
    gate=GateCondition(who={"admin"}),
    payload={"check": "permissions"}
)

action = LatentSymbol(
    id="delete_action",
    symbol_type="ACTION:delete",
    gate=GateCondition(who={"admin"}),
    payload={"target": "resource_123"}
)

engine.register(gate)
engine.register(action)

# Compose with >> operator
guarded = sym(gate) >> sym(action)

# Admin passes gate, action runs
admin_ctx = Context(who="admin", when=datetime.now(), where="app", state={})
result = guarded.try_bind(admin_ctx, engine)
# result.bound.symbol_id == "delete_action"

# User fails at gate, action never attempted
user_ctx = Context(who="user", when=datetime.now(), where="app", state={})
result = guarded.try_bind(user_ctx, engine)
# result.is_bound == False, result.source.id == "auth_gate"
```

Chain multiple steps:

```python
validated = sym(auth) >> sym(validate) >> sym(execute)
```

---

## Pattern 11: Parallel Requirements

All symbols must bind for success.

```python
from bindlang import LatentSymbol, GateCondition, Context, BindingEngine, sym
from datetime import datetime

engine = BindingEngine()

# All three approvals needed
approval_a = LatentSymbol(
    id="approval_a",
    symbol_type="APPROVAL:a",
    gate=GateCondition(who={"manager"}),
    payload={"approver": "a"}
)

approval_b = LatentSymbol(
    id="approval_b",
    symbol_type="APPROVAL:b",
    gate=GateCondition(who={"manager"}),
    payload={"approver": "b"}
)

approval_c = LatentSymbol(
    id="approval_c",
    symbol_type="APPROVAL:c",
    gate=GateCondition(who={"manager"}),
    payload={"approver": "c"}
)

engine.register(approval_a)
engine.register(approval_b)
engine.register(approval_c)

# Compose with & operator
all_approvals = sym(approval_a) & sym(approval_b) & sym(approval_c)

# Manager can satisfy all
manager_ctx = Context(who="manager", when=datetime.now(), where="app", state={})
result = all_approvals.try_bind(manager_ctx, engine)
# result.is_bound == True
# result.bound_all contains all three BoundSymbols
```

---

## Pattern 12: Mixed Composition

Combine operators for complex workflows.

```python
from bindlang import LatentSymbol, GateCondition, Context, BindingEngine, sym
from datetime import datetime

engine = BindingEngine()

# Setup symbols
admin_gate = LatentSymbol(id="admin_gate", symbol_type="GATE:admin", gate=GateCondition(who={"admin"}), payload={})
user_gate = LatentSymbol(id="user_gate", symbol_type="GATE:user", gate=GateCondition(who={"user"}), payload={})
validate = LatentSymbol(id="validate", symbol_type="CHECK:validate", gate=GateCondition(who={"user", "admin"}), payload={})
execute = LatentSymbol(id="execute", symbol_type="ACTION:execute", gate=GateCondition(who={"user", "admin"}), payload={})

for s in [admin_gate, user_gate, validate, execute]:
    engine.register(s)

# Complex workflow: (admin OR user gate) THEN (validate AND execute)
workflow = (sym(admin_gate) | sym(user_gate)) >> (sym(validate) & sym(execute))

user_ctx = Context(who="user", when=datetime.now(), where="app", state={})
result = workflow.try_bind(user_ctx, engine)
# Falls back to user_gate, then runs both validate and execute in parallel
```

---

## Next Steps

- [Models](models.md) - Understand core types
- [BindingEngine](engine.md) - Explore all methods
- [Orchestration](orchestration.md) - Multi-actor patterns and API
- [Templates](templates.md) - Add validation to patterns
- [Debugging](debugging.md) - Debug when patterns don't work
