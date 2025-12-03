# State Mutations in bindlang

**State-driven cascade execution**

---

## Overview

State mutations enable symbols to create preconditions for other symbols dynamically during cascade execution. When a symbol binds and produces a `state_mutation` effect, that mutation is applied to the context, making it available for subsequent symbols in the same cascade.

---

## Basic Example

```python
from bindlang import BindingEngine, LatentSymbol, GateCondition, Context
from datetime import datetime

engine = BindingEngine()

# Symbol 1: Pick up key (sets has_key=True)
pick_up_key = LatentSymbol(
    id="pick_up_key",
    symbol_type="ACTION:pickup",
    gate=GateCondition(who={"player"}),
    payload={"state_mutation": {"has_key": True}}
)

# Symbol 2: Unlock door (requires has_key=True)
unlock_door = LatentSymbol(
    id="unlock_door",
    symbol_type="ACTION:unlock",
    gate=GateCondition(who={"player"}, state={"has_key": True}),
    payload={"state_mutation": {"door_locked": False}}
)

engine.register(pick_up_key)
engine.register(unlock_door)

# Initial context: no key
context = Context(
    who="player",
    where="room",
    when=datetime.now(),
    state={"has_key": False, "door_locked": True}
)

# Execute cascade
bound, final_context = engine.bind_all_registered(context)

# Result:
# Round 1: pick_up_key binds → sets has_key=True
# Round 2: unlock_door sees has_key=True → binds
# Final state: {"has_key": True, "door_locked": False}
```

---

## How It Works

### Pre-Check 3: State Conditions

Before attempting to bind a symbol, the engine checks if `gate.state` conditions are satisfied:

```python
# Symbol with state requirement
unlock_door = LatentSymbol(
    gate=GateCondition(state={"has_key": True}),
    ...
)

# PRE-CHECK 3: State conditions met?
if context.state.get("has_key") != True:
    # Symbol remains LATENT (not attempted)
    continue
```

**Behavior:**
- If state conditions NOT met → Symbol remains **LATENT** (never attempted)
- If state conditions met → Symbol is attempted (may BIND or FAIL on other gates)

This is consistent with dependency and temporal pre-checks.

### Reactive State Mutations (Default)

By default, state mutations are applied between cascade rounds:

```python
# Default behavior (apply_state_mutations=True)
bound, final_context = engine.bind_all_registered(context)

# What happens:
# Round 1:
#   - pick_up_key binds
#   - State mutation: has_key=True applied to context
# Round 2:
#   - unlock_door checks: state.has_key == True? Yes!
#   - unlock_door binds
```

### Analytical Mode (Opt-Out)

For analysis without side effects, disable state mutations:

```python
# Analytical mode (apply_state_mutations=False)
bound, final_context = engine.bind_all_registered(
    context,
    apply_state_mutations=False
)

# What happens:
# Round 1:
#   - pick_up_key binds
#   - State mutation recorded in effect but NOT applied
# Round 2:
#   - unlock_door checks: state.has_key == False (original)
#   - unlock_door remains LATENT (state condition not met)
```

---

## State Conflict Behavior

**If multiple symbols in the SAME round mutate the same state key:**

### Last-Write-Wins

The final value is determined by execution order (last write wins).

```python
# Both bind in Round 1:
symbol_a = LatentSymbol(
    id="heal",
    payload={"state_mutation": {"health": 100}}
)

symbol_b = LatentSymbol(
    id="damage",
    payload={"state_mutation": {"health": 50}}
)

# Result: health = 50 (last write wins)
# No error or warning is raised
```

### Handling Conflicts

**If order matters, use dependencies:**

```python
# Ensure damage happens AFTER heal
symbol_b = LatentSymbol(
    id="damage",
    payload={"state_mutation": {"health": 50}},
    depends_on=["heal"]  # Forces ordering
)

# Now: heal runs in Round 1, damage in Round 2 (or later)
```

**Alternative: Use state conditions:**

```python
# Only damage if health > 75
symbol_b = LatentSymbol(
    id="damage",
    gate=GateCondition(state={"health": 100}),  # Specific value check
    payload={"state_mutation": {"health": 50}}
)
```

---

## Audit Trail for State Changes

State mutations are tracked in the audit trail with old→new values:

```python
bound, final_context = engine.bind_all_registered(context)

# Check state changes for a symbol
pick_up = next(s for s in bound if s.symbol_id == "pick_up_key")
print(pick_up.state_changes_applied)
# Output:
# [{"key": "has_key", "old": False, "new": True}]
```

**Structure:**
```python
{
    "symbol_id": "pick_up_key",
    "success": True,
    "effect": {
        "state_mutation": {"has_key": True}  # Intent
    },
    "state_changes_applied": [  # Actual changes
        {"key": "has_key", "old": False, "new": True}
    ]
}
```

This allows you to see:
- **Intent:** What the symbol wanted to change (`effect.state_mutation`)
- **Actual:** What actually changed (`state_changes_applied` with old→new values)

---

## Multi-Step State Chains

State mutations enable multi-step workflows:

```python
# Three-step chain: A → B → C
step_a = LatentSymbol(
    id="step_a",
    gate=GateCondition(who={"user"}),
    payload={"state_mutation": {"x": 1}}
)

step_b = LatentSymbol(
    id="step_b",
    gate=GateCondition(who={"user"}, state={"x": 1}),
    payload={"state_mutation": {"y": 2}}
)

step_c = LatentSymbol(
    id="step_c",
    gate=GateCondition(who={"user"}, state={"y": 2}),
    payload={"state_mutation": {"z": 3}}
)

# Result:
# Round 1: step_a binds → x=1
# Round 2: step_b binds → y=2
# Round 3: step_c binds → z=3
# Final state: {"x": 1, "y": 2, "z": 3}
```

---

## Context Immutability

Context is **immutable** (frozen Pydantic model). State mutations create **new Context instances**:

```python
# Original context unchanged
original_context = Context(who="user", state={"x": 0}, ...)
bound, final_context = engine.bind_all_registered(original_context)

print(original_context.state)  # {"x": 0} (unchanged)
print(final_context.state)      # {"x": 1} (new context)
```

**Functional programming style:** No mutation of input, new context returned.

---

## Max Iterations Safety

Cascade stops after `max_iterations` rounds (default 10):

```python
# Potential infinite loop:
symbol_a = LatentSymbol(
    gate=GateCondition(state={"x": 1}),
    payload={"state_mutation": {"x": 2}}
)

symbol_b = LatentSymbol(
    gate=GateCondition(state={"x": 2}),
    payload={"state_mutation": {"x": 1}}
)

# Safe: stops after 10 rounds (configurable)
bound, final = engine.bind_all_registered(context, max_iterations=10)
```

---

## Usage Guidelines

### State for Dynamic Conditions

```python
# Dynamic "has collected 3 items" check
gate=GateCondition(state={"items_collected": 3})

# Alternative: Dependencies (if collection is fixed order)
depends_on=["collect_item_1", "collect_item_2", "collect_item_3"]
```

### Dependencies for Ordering

```python
# Use dependencies when order matters
symbol_b.depends_on = ["symbol_a"]  # Forces sequence
```

### Tracking State Changes

```python
# Inspect state changes after binding
for symbol in bound:
    if symbol.state_changes_applied:
        print(f"{symbol.symbol_id} changed: {symbol.state_changes_applied}")
```

### Analytical Mode

```python
# Evaluate without applying mutations
potential_bound, _ = engine.bind_all_registered(
    context,
    apply_state_mutations=False
)
print(f"Would bind: {[s.symbol_id for s in potential_bound]}")
```

---

## Comparison with Dependencies

| Feature | State Mutations | Dependencies |
|---------|----------------|--------------|
| **Dynamic conditions** | Yes (state can have any value) | No (fixed symbol IDs) |
| **Ordering** | Last-write-wins (same round) | Enforced (different rounds) |
| **Flexibility** | High (key from multiple sources) | Low (specific symbol) |
| **Clarity** | Intent clear in gate.state | Order clear in depends_on |

**When to use state:**
- Condition can be satisfied by multiple sources
- Value-based logic ("gold >= 100")
- Game state, workflow state

**When to use dependencies:**
- Specific sequence required
- One symbol must complete before another
- Ordering matters

See [When to Use What](when-to-use-what.md) for complete mechanism comparison.

---

## Common Patterns

### Game Mechanics
```
# Pick up weapon enables attack
pick_sword: payload.state_mutation = {has_weapon: true}
attack:     gate.state = {has_weapon: true}
```

### Resource Management
```
# Purchase sets gold, upgrade requires exact value
purchase:    payload.state_mutation = {gold: 400}
buy_upgrade: gate.state = {gold: 400}
```

### Progressive Unlock
```
# Sequential task completion
task_a: payload.state_mutation = {progress: 1}
task_b: gate.state = {progress: 1}, payload.state_mutation = {progress: 2}
task_c: gate.state = {progress: 2}, payload.state_mutation = {progress: 3}
```

---

## See Also

- [Engine Reference](../reference/engine.md)
- [Audit Trail](../reference/audit-trail.md)
- [When to Use What](when-to-use-what.md)
