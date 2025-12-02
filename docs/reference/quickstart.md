# Quick Start

[Back to Reference](index.md)

---

## Basic Usage

```python
from bindlang import LatentSymbol, GateCondition, Context, BindingEngine
from datetime import datetime

# Create symbol with activation conditions
symbol = LatentSymbol(
    id="vote_promote",
    symbol_type="VOTE:promote",
    gate=GateCondition(who={"admin"}, where={"production"}),
    payload={"target": "alice", "weight": 1.0}
)

# Register with engine
engine = BindingEngine()
engine.register(symbol)

# Attempt binding against context
context = Context(who="admin", when=datetime.now(), where="production", state={})
result = engine.bind(symbol, context)

if result:
    print(f"Activated: {result.effect}")
    # Output: Activated: {'target': 'alice', 'weight': 1.0}
else:
    print(engine.audit.explain("vote_promote"))
```

The symbol activates because context satisfies gate conditions (who=admin, where=production). The payload becomes the effect.

---

## Context-Dependent Binding

Same symbol, different context produces different outcome:

```python
# Regular user in development environment
user_context = Context(who="bob", when=datetime.now(), where="development", state={})
result = engine.bind(symbol, user_context)  # Returns None

# Audit trail shows why binding failed
print(engine.audit.explain("vote_promote"))
# Output:
# Symbol 'vote_promote' failed to activate:
#   - who: 'bob' not in ['admin']
#   - where: 'development' not in ['production']
```

This is the core of bindlang: symbols carry dormant meaning that activates conditionally based on runtime context.

---

## Advanced: Dependency Cascade

Symbols activate in dependency order across multiple rounds.

```python
from bindlang import LatentSymbol, GateCondition, Context, BindingEngine
from datetime import datetime

engine = BindingEngine()

# Create dependency chain: A → B → C
symbols = [
    LatentSymbol(
        id="symbol_a",
        symbol_type="STEP:first",
        gate=GateCondition(who={"system"}),
        payload={"step": "first"}
    ),
    LatentSymbol(
        id="symbol_b",
        symbol_type="STEP:second",
        gate=GateCondition(who={"system"}),
        payload={"step": "second"},
        depends_on=["symbol_a"]
    ),
    LatentSymbol(
        id="symbol_c",
        symbol_type="STEP:third",
        gate=GateCondition(who={"system"}),
        payload={"step": "third"},
        depends_on=["symbol_b"]
    )
]

for sym in symbols:
    engine.register(sym)

# Bind all - engine handles cascade automatically
context = Context(who="system", when=datetime.now(), where="zone", state={})
activated = engine.bind_all_registered(context)

print(f"Activated {len(activated)} symbols")
# Output: Activated 3 symbols

for bound in activated:
    print(f"{bound.symbol_id}: {bound.effect}")
# Output:
# symbol_a: {'step': 'first'}
# symbol_b: {'step': 'second'}
# symbol_c: {'step': 'third'}
```

`bind_all_registered()` resolves dependencies automatically. Symbols activate in rounds based on dependency depth.

---

## Advanced: Multi-Dimensional Gates

Complex gate conditions across all four dimensions.

```python
from bindlang import LatentSymbol, GateCondition, Context, BindingEngine
from datetime import datetime

engine = BindingEngine()

# Symbol requiring specific who, where, and state
complex_gate = LatentSymbol(
    id="secure_action",
    symbol_type="ACTION:secure",
    gate=GateCondition(
        who={"admin", "moderator"},
        where={"production"},
        state={"verified": True}
    ),
    payload={"action": "execute"}
)
engine.register(complex_gate)

# Context fails all conditions
fail_context = Context(
    who="alice",
    when=datetime.now(),
    where="development",
    state={"verified": False}
)

result = engine.bind(complex_gate, fail_context)
# result is None

# Detailed explanation of all failures
print(engine.audit.explain("secure_action"))
# Output:
# Symbol 'secure_action' failed to activate:
#   - who: 'alice' not in ['admin', 'moderator']
#   - where: 'development' not in ['production']
#   - state['verified']: expected True, got False
```

Audit trail provides structured failure reasons for debugging and UI display.

---

## Next Steps

- [Models](models.md) - Learn all core types
- [BindingEngine](engine.md) - Explore binding methods
- [Common Patterns](patterns.md) - See practical examples
- [Audit Trail](audit-trail.md) - Debug failures effectively
