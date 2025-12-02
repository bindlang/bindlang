# Choosing the Right Mechanism

Quick reference for selecting appropriate bindlang patterns and gates.

---

## Core Mechanisms

| Mechanism | Use When | Key Characteristic | Example |
|-----------|----------|-------------------|---------|
| **`depends_on`** | Specific sequence required | Enforced ordering across rounds | `symbol_b.depends_on = ["symbol_a"]` |
| **`gate.state`** | Dynamic value-based condition | Flexible, multiple sources | `gate.state = {"gold": 100}` |
| **`gate.who`** | Actor ownership/accountability | Specific performer required | `gate.who = {"admin"}` |
| **`gate.where`** | Location-based filtering | Environment/zone restriction | `gate.where = {"production"}` |
| **`gate.when`** | Temporal constraints | Time-based activation | `gate.when = "after:2024-01-01"` |
| **`ActorSequenceRunner`** | Multi-actor coordination | Witness semantics preserved | `runner.run_actor_sequence(contexts)` |

---

## Decision Matrix

### Ordering vs Conditions

| Requirement | Solution |
|-------------|----------|
| Symbol A must complete before B (fixed) | `depends_on` |
| Symbol can activate if state value matches (dynamic) | `gate.state` |
| Both symbols can run in parallel | Neither (no ordering needed) |

### Actor Patterns

| Scenario | Mechanism |
|----------|-----------|
| Only specific actor can perform action | `gate.who` |
| Track which actors are present | `gate.state` (e.g., `alice_present: True`) |
| Sequential actions by different actors | `ActorSequenceRunner` |
| Multiple actors must complete before next step | `gate.state` + state mutations |

### State vs Dependencies

| Need | Use |
|------|-----|
| Condition satisfied by multiple sources | `gate.state` |
| Condition satisfied by one specific symbol | `depends_on` |
| Value-based logic (thresholds, counts) | `gate.state` |
| Strict sequence (A then B then C) | `depends_on` |

---

## Common Scenarios

### Game Mechanics
```
# Collect key before unlocking door
pick_up_key:  payload.state_mutation = {has_key: true}
unlock_door:  gate.state = {has_key: true}
```

### Approval Workflow
```
# Two approvers required
approve_1:       payload.state_mutation = {approvals: 1}
approve_2:       gate.state = {approvals: 1}, payload.state_mutation = {approvals: 2}
final_approval:  gate.state = {approvals: 2}
```

### Multi-Actor Collaboration
```
# Both actors must complete their parts
alice_part:    gate.who = {alice}, payload.state_mutation = {alice_done: true}
bob_part:      gate.who = {bob}, payload.state_mutation = {bob_done: true}
collaboration: gate.state = {alice_done: true, bob_done: true}
```

### Fixed Sequence
```
# Step 1 must complete before step 2
step_1: (no dependencies)
step_2: depends_on = [step_1]
step_3: depends_on = [step_2]
```

---

## Combining Mechanisms

Multiple mechanisms can be combined in a single gate:

```python
gate = GateCondition(
    who={"admin"},              # Actor requirement
    where={"production"},       # Location requirement
    state={"verified": True},   # State requirement
    when="after:2024-01-01"     # Temporal requirement
)
```

All conditions must pass (implicit AND).

---

## Performance Considerations

| Mechanism | Performance Impact |
|-----------|-------------------|
| `depends_on` | Adds rounds to cascade (one round per dependency level) |
| `gate.state` | Pre-check prevents binding attempt (efficient) |
| `gate.who` | Pre-check prevents binding attempt (efficient) |
| `ActorSequenceRunner` | Sequential context execution (O(n) actors) |

---

## See Also

- [State Mutations](state-mutations.md) - Detailed comparison with dependencies
- [Orchestration Reference](../reference/orchestration.md) - ActorSequenceRunner API
- [Models Reference](../reference/models.md) - GateCondition semantics
- [Common Patterns](../reference/patterns.md) - Working examples
