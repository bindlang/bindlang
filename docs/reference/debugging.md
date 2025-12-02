# Debugging

[Back to Reference](index.md)

Use audit trail and diagnostics to understand symbol behavior.

---

## Symbol Activation Failures

### explain()

```python
from bindlang import BindingEngine, LatentSymbol, GateCondition, Context
from datetime import datetime

engine = BindingEngine()

symbol = LatentSymbol(
    id="admin_action",
    symbol_type="ACTION:promote",
    gate=GateCondition(who={"admin"}, where={"production"}),
    payload={"target": "alice"}
)
engine.register(symbol)

# Try to bind as regular user
context = Context(who="bob", when=datetime.now(), where="development", state={})
result = engine.bind(symbol, context)

# Why didn't it activate?
print(engine.audit.explain("admin_action"))
# Output:
# Symbol 'admin_action' failed to activate:
#   - who: 'bob' not in ['admin']
#   - where: 'development' not in ['production']
```

---

## Structured Failure Analysis

### failed()

```python
failures = engine.audit.failed("admin_action")

for attempt in failures:
    print(f"\nFailed at: {attempt.attempt_timestamp}")
    print(f"Context: who={attempt.context_snapshot['who']}, where={attempt.context_snapshot['where']}")

    for reason in attempt.failure_reasons:
        print(f"  {reason.condition_type}: {reason.message}")
        print(f"    Expected: {reason.expected}")
        print(f"    Actual: {reason.actual}")

# Output:
# Failed at: 2024-01-15 10:30:00
# Context: who=bob, where=development
#   who: who: 'bob' not in ['admin']
#     Expected: {'admin'}
#     Actual: 'bob'
#   where: where: 'development' not in ['production']
#     Expected: {'production'}
#     Actual: 'development'
```

---

## Aggregate Statistics

### stats()

```python
stats = engine.audit.stats()
print(stats)
# Output: {"who": 15, "dependency": 42, "state": 8, "when": 3}

# Identify bottleneck
most_common = max(stats.items(), key=lambda x: x[1])
print(f"Most common failure: {most_common[0]} ({most_common[1]} times)")
# Output: Most common failure: dependency (42 times)
```

**Failure types:**
- `who` - Actor not in allowed set
- `where` - Location not in allowed set
- `when` - Temporal condition not met
- `state` - State condition not met
- `dependency` - Dependent symbol not activated
- `expired` - Deadline passed

---

## State Transitions

### get_ledger()

```python
# Get transitions for specific symbol
transitions = engine.get_ledger("admin_action")
for t in transitions:
    print(f"{t.timestamp}: {t.from_state} → {t.to_state} ({t.reason})")

# Output:
# 2024-01-15 10:00:00: CREATED → DORMANT (Registered)
# 2024-01-15 10:30:00: DORMANT → ACTIVATED (Binding success)

# Get all transitions
all_transitions = engine.get_ledger()
```

---

## Export for Analysis

```python
# Export failures to file for external analysis
count = engine.export.failures("failures.json")
print(f"Exported {count} failures")

# Analyze with pandas, jq, etc.
# $ jq '.[] | select(.failure_reasons[0].condition_type == "who")' failures.json
```

```python
# Full audit trail
engine.export.trail("audit.json")

# JSONL format for streaming analysis
engine.export.trail("audit.jsonl", fmt="jsonl")
```

---

## Streaming Mode Debugging

```python
# Enable streaming mode
with BindingEngine(audit_file="live_audit.jsonl") as engine:
    # Register and bind...
    pass

# In another terminal, monitor live:
# $ tail -f live_audit.jsonl | jq 'select(.success == false)'
```

---

## Event Hooks

```python
def debug_hook(symbol, context, bound_symbol):
    print(f"[DEBUG] Activated: {symbol.id}")
    print(f"  Who: {context.who}")
    print(f"  Where: {context.where}")
    print(f"  Effect: {bound_symbol.effect}")

engine = BindingEngine(on_symbol_activated=debug_hook)
```

---

## Common Issues

### Issue 1: Dependency Not Resolved

**Symptom:** Symbol never activates despite conditions met

**Debug:**
```python
failures = engine.audit.failed("symbol_id")
for f in failures:
    for r in f.failure_reasons:
        if r.condition_type == "dependency":
            print(f"Waiting for: {r.expected}")
```

**Solution:** Check if dependent symbols are registered and can activate

---

### Issue 2: Temporal Condition Always Fails

**Symptom:** `when` condition never passes

**Debug:**
```python
symbol = engine.symbol_registry["symbol_id"]
print(f"Gate when: {symbol.gate.when}")

context = ...  # your context
print(f"Context when: {context.when}")
```

**Common mistakes:**
- ISO datetime format incorrect
- Using `after` when you mean `before`
- State key doesn't exist for symbolic references

---

### Issue 3: Circular Dependencies

**Symptom:** `CircularDependencyError` on registration

**Debug:**
```python
try:
    engine.register(symbol)
except CircularDependencyError as e:
    print(e)
    # Output: Circular dependency detected: a → b → c → a

# Solution: Break the cycle
```

**Solution:** Redesign dependency chain to be acyclic

---

### Issue 4: State Condition Not Met

**Symptom:** State-based gates never pass

**Debug:**
```python
symbol = engine.symbol_registry["symbol_id"]
print(f"Required state: {symbol.gate.state}")

context = ...
print(f"Actual state: {context.state}")

# Check exact match
for key, expected in symbol.gate.state.items():
    actual = context.state.get(key)
    match = actual == expected
    print(f"{key}: expected={expected}, actual={actual}, match={match}")
```

**Common mistakes:**
- State key missing in context
- Type mismatch (e.g., `1` vs `"1"`)
- State not updated between rounds

---

## Type Checking

```bash
mypy your_code.py
```

---

## Next Steps

- [BindingEngine](engine.md) - Understand audit trail API
- [Common Patterns](patterns.md) - See working examples
- [Models](models.md) - Review core types
