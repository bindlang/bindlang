# Stress Testing bindlang

Stress tests examining bindlang behavior under extreme conditions. Tests clarify semantic boundaries and document edge case handling.

**Test coverage:**
- Oscillation detection and max_iterations protection
- Long dependency chains and cascade completion
- Multi-actor resource conflicts and fairness
- Circular dependency detection
- State explosion scalability
- Sequential execution model
- Temporal gate behavior
- Reusable symbols with dependencies

---

## Test 1: Oscillation Detection

**Purpose:** Test whether reusable consumption mode handles oscillating state mutations and respects max_iterations.

**Scenario:**
```json
{
  "symbols": [
    {
      "id": "toggle_on",
      "consumption": "reusable",
      "gate": {"state": {"flag": false}},
      "payload": {"state_mutation": {"flag": true}}
    },
    {
      "id": "toggle_off",
      "consumption": "reusable",
      "gate": {"state": {"flag": true}},
      "payload": {"state_mutation": {"flag": false}}
    }
  ]
}
```

**Expected behavior:**
- Oscillation pattern: ON → OFF → ON → OFF...
- Stops at max_iterations (10)
- No infinite loop
- Deterministic outcome

**Results:**
- 10 bindings (perfect alternation)
- Pattern: `toggle_on → toggle_off → toggle_on → toggle_off → ...`
- Stopped at round 10 (max_iterations respected)
- Final state: `flag=false` (deterministic)

**Key findings:**
1. Reusable consumption enables symbols to bind multiple times
2. max_iterations provides protection against infinite loops
3. State mutations cascade correctly - each round sees updated state
4. Oscillation follows deterministic pattern across executions

---

## Test 2: Long Dependency Chain vs max_iterations

**Purpose:** Test how bindlang handles long dependency chains and whether max_iterations truncates productive cascades.

**Scenario:**
```python
# 15-step chain: step_01 → step_02 → ... → step_15
# Each step depends on previous step
# Default max_iterations=10
```

**Expected behavior:**
- Initially: 10 steps bound, 5 latent (truncation at max_iterations)
- After analysis: All 15 steps bound (progress each round)

**Results:**
- 15 bindings (all steps)
- 15 rounds (one per step)
- All state mutations applied
- 0 latent (full completion)

**Key findings:**
1. **max_iterations = max rounds with progress**, not max bindings total
2. Dependency chains execute to completion - each round has progress
3. State mutations in chains propagate correctly - all 15 steps receive updates
4. No truncation when productive work continues

**Semantic insight:** max_iterations protects against deadlocks (no progress, latent symbols remain) and oscillation (progress without endpoint), but not against dependency chains (intentional progress toward completion).

---

## Test 3: Actor Sequence Ordering

**Purpose:** Test whether actor_sequence order deterministically determines outcomes during resource competition.

**Scenario:**
```python
# Resource: 1 slot available
# Actors: Alice, Bob (both want to register)
# Test A: Alice first → Bob first
# Test B: Bob first → Alice first
```

**Expected behavior:**
- Sequence A→B: Alice gets slot, Bob waitlisted
- Sequence B→A: Bob gets slot, Alice waitlisted
- Different outcomes based on ordering
- Resource constraint respected

**Results:**

Sequence A→B:
- `alice_registered=True, bob_on_waitlist=True`
- `slots_available=0`

Sequence B→A:
- `bob_registered=True, alice_on_waitlist=True`
- `slots_available=0`

**Key findings:**
1. Actor sequence is deterministic policy - order determines outcome
2. Multi-actor state mutations work correctly - state shared between perspectives
3. Resource constraints respected - when slot taken, becomes unavailable
4. First-come-first-served via sequence ordering (transparent but not necessarily fair)

**Design implication:** Actor sequence is not merely technical implementation - it represents semantic policy for resource allocation, conflict resolution, and fairness models.

---

## Test 4: Circular Dependency Detection

**Purpose:** Test whether bindlang detects circular dependencies and prevents deadlocks.

**Scenario:**
```python
# A → B → C → A (circular dependency)
symbol_a = LatentSymbol(id="symbol_a", depends_on=["symbol_c"])
symbol_b = LatentSymbol(id="symbol_b", depends_on=["symbol_a"])
symbol_c = LatentSymbol(id="symbol_c", depends_on=["symbol_b"])
```

**Expected behavior:**
- CircularDependencyError raised at registration
- Full cycle path shown in error message
- System protected from deadlock

**Results:**
- Exception raised: "Circular dependency detected: symbol_a → symbol_b → symbol_c → symbol_a"
- Fast failure - detected at registration, not execution
- Full cycle path provided in error message
- System protected from silent deadlock

**Key findings:**
- bindlang has built-in circular dependency detection
- Detection occurs at registration (fail-fast), not execution
- Error messages include complete cycle path for debugging
- Prevents silent deadlocks through early detection

---

## Test 5: State Explosion

**Purpose:** Test state management scalability under massive state mutation load.

**Scenario:**
```python
# 10 symbols × 10 state keys = 100 state mutations
for i in range(10):
    symbol = LatentSymbol(
        id=f"symbol_{i}",
        payload={"state_mutation": {
            f"key_{i}_{j}": f"val_{i}_{j}" for j in range(10)
        }}
    )
```

**Expected behavior:**
- All 100 state keys present in final_state
- All values correct
- No memory leaks or performance degradation

**Results:**
- 10 symbols × 10 keys = 100 state mutations
- All 100 keys present in final_state
- All values correct (val_X_Y format)
- No memory leaks or degradation observed

**Key findings:**
- State management scales linearly - handles 100 mutations without performance issues
- Context.with_state_update() handles load without degradation
- No bottlenecks observed in state propagation mechanism

---

## Test 6: Diamond Dependency Pattern

**Purpose:** Test multi-dependency resolution with convergent pattern (A → B+C → D).

**Scenario:**
```python
# A (root)
# ├─ B (depends on A)
# ├─ C (depends on A)
# └─ D (depends on B and C)
```

**Expected behavior:**
- All 4 symbols bind
- D binds only after both B and C complete
- Execution order respects multi-dependency

**Results:**
- All 4 symbols bound
- 4 rounds (sequential: A → B → C → D)
- Multi-dependency works: D requires both B and C
- All state mutations applied

**Key findings:**
- **Sequential execution model:** Symbols bind one-per-round even when multiple have satisfied dependencies
- B and C (both depend only on A) bind in separate rounds, not parallel
- This is correct behavior - bindlang execution is deterministic and sequential, not concurrent
- Provides predictable ordering and eliminates race conditions

**Design note:** For concurrent execution patterns, implement parallelism at application level (multiple bindlang instances, symbol partitioning, or event sourcing). Library maintains simplicity through sequential model.

---

## Test 7: Multi-Actor Resource Conflict

**Purpose:** Test multi-actor coordination with N>2 actors competing for limited resources.

**Scenario:**
```python
# 3 actors (Alice, Bob, Charlie) competing for 2 slots
actor_contexts = [
    {"who": None, "where": "office"},       # System: registration opens
    {"who": "alice", "where": "office"},    # Alice attempts
    {"who": "bob", "where": "office"},      # Bob attempts
    {"who": "charlie", "where": "office"}   # Charlie attempts
]
```

**Expected behavior:**
- First 2 actors in sequence register successfully
- Third actor waitlisted (slots full)
- Resource allocation deterministic via actor sequence

**Results:**
- Alice and Bob registered (first 2 in sequence)
- Charlie waitlisted (slots full)
- Actor sequence deterministically allocates resources
- N>2 actor scaling works correctly

**Key findings:**
- **Within-perspective state mutations:** State mutations apply between rounds, not within same round
- Initial implementation had waitlist duplication because register and waitlist symbols both checked same initial context
- Solution: Add proper state gates (`slots_available=0` for waitlist symbols)
- Documentation updated in orchestration.md to clarify within-perspective execution

---

## Test 8: Temporal Cascade

**Purpose:** Test mixing of temporal gates with state mutations in cascade pattern.

**Scenario:**
```json
{
  "08:00": "morning_startup (temporal) → system_ready=true",
  "09:00": "calibration (temporal + system_ready) → calibration_done=true",
  "10:00": "experiment_prep (temporal + calibration_done) → experiment_ready=true",
  "11:00": "run_experiment (temporal + experiment_ready) → experiment_complete=true",
  "Dec 25": "too_early_event → should remain latent"
}
```

**Context time:** 12:00 (after all temporal gates except Dec 25)

**Expected behavior:**
- First 4 symbols bind (cascade completes)
- Dec 25 event remains latent (future temporal gate)
- Temporal pre-checks filter future events
- State mutations applied in order

**Results:**
- 4 symbols bound (morning_startup → calibration → experiment_prep → run_experiment)
- 1 latent (too_early_event correctly filtered)
- 4 rounds (sequential cascade)
- All state mutations applied: system_ready, calibration_done, experiment_ready, experiment_complete

**Key findings:**
1. Temporal pre-checks work correctly - future events filtered before binding attempts
2. Temporal + state mixing supported - symbols can require both temporal AND state conditions
3. Cascade with temporal gates - temporal conditions do not break dependency chains
4. Latent reasons accurate - future event shows temporal gate failure as reason

---

## Test 9: Reusable Symbols with Dependencies

**Purpose:** Test that reusable symbols with depends_on respect dependencies and can bind multiple times after dependency satisfaction.

**Scenario:**
```python
# initialization (one_shot) → phase="ready"
# phase_a (reusable, depends_on init) → phase="A"
# phase_b (reusable, depends_on init) → phase="B"
# phase_c (reusable, depends_on init) → phase="C"
# reset_to_ready (reusable, depends_on init) → phase="ready"
# Creates cycle: ready → A → B → C → ready → A → B → C...
```

**Expected behavior:**
- Round 1: initialization binds (enables all dependencies)
- Round 2+: Cycle repeats based on state gates
- Reusable symbols bind multiple times
- One-shot initialization binds exactly once

**Results:**
- 10 bindings total (10 rounds, max_iterations)
- Perfect cycle: init → A → B → C → ready → A → B → C → ready → A
- All 5 symbols bound at least once
- initialization bound exactly 1 time (one_shot respected)
- phase_a, phase_b, phase_c, reset_to_ready all bound 2+ times

**Key findings:**
1. **depends_on is one-time gate** - Once satisfied, reusable symbols can bind repeatedly
2. Reusable respects dependencies - No binding before dependency satisfied
3. One-shot + reusable mixing works - One one_shot symbol can serve as dependency for multiple reusable symbols
4. State gates + depends_on - Both constraints evaluated correctly (AND logic)

---

## Cross-Test Insights

### State Mutation Consistency

All tests demonstrate consistent state mutation behavior:
- Applied **between rounds** (not within same round)
- Propagate correctly to next iteration
- Follow **last-write-wins** for conflicts within same round
- Deterministic (same input produces same output)

### Consumption Mode Flexibility

- **one_shot** (default): Narratives, workflows, unique events
- **reusable**: Automation, iterations, rule engines
- Can be mixed within same scenario

### Multi-Actor Behavior

ActorSequenceRunner demonstrates:
- Stable behavior during resource competition
- Deterministic outcomes with different orderings
- Correct state sharing between actor perspectives

### max_iterations Protection

Prevents:
- Oscillation (Test 1) - PROTECTED
- Deadlocks (theoretical) - PROTECTED
- Productive chains (Test 2) - NOT PREVENTED (correct behavior)

---

## Performance Observations

### Oscillation Test (10 iterations)
- Execution: < 50ms
- Memory: Linear with number of bindings
- Audit trail: 10 entries

### Long Chain Test (15 steps)
- Execution: < 100ms
- Memory: Linear with chain length
- Audit trail: 15 entries

### Actor Ordering Test (2x5 bindings)
- Execution: < 150ms (two runs)
- Memory: Linear with (actors × steps)
- Audit trail: 2×5 entries

**Conclusion:** Linear scaling, no memory leaks, fast execution across all tests.

---

## Edge Case Behavior

### Reusable + max_iterations = Controlled Oscillation
Intentional design - prevents infinite loops while allowing iterations.

### Dependency Chain Completion
max_iterations does not prevent productive chains - workflows with progress in each round continue to completion.

### Actor Sequence as Policy
Not merely execution order - represents semantic model for fairness, resource allocation, and conflict resolution.

---

## Recommendations

### Set Explicit max_iterations

Based on use case:
- **Narratives:** 50-100 (generous for chains)
- **Automation:** 10-20 (limit oscillation)
- **Analysis:** 1000+ (allow deep exploration)

### Monitor Audit Trail Size

Audit trail grows linearly with iterations - consider storage implications for long-running systems.

### Use Consumption Modes Strategically

- Default to `one_shot` for safety
- Use `reusable` explicitly only when intentional
- Document why reusable is needed in comments

### Actor Sequence Design

- Document fairness policy explicitly
- Consider randomization for fairness
- Use deterministic ordering for reproducibility

---

## Additional Test Scenarios

Other test scenarios for exploring bindlang behavior:
- **Massive parallelism** - 100+ actors in same scenario
- **Deep nesting** - State mutations that trigger cascading state mutations
- **Memory stress** - 10,000+ symbols in registry
- **Temporal boundary conditions** - Timezone handling, leap seconds, DST transitions

---

## Observed Characteristics

Tests demonstrate consistent behavior across scenarios:

- **Deterministic** - Same input produces same output
- **Protected** - max_iterations prevents infinite loops
- **Flexible** - Consumption modes enable different semantics
- **Multi-actor capable** - Actor sequences function as policy
- **Performant** - Linear scaling, no degradation

---

**Related documentation:**
- [BindingEngine API](../reference/engine.md) - Core runtime and max_iterations
- [Orchestration](../reference/orchestration.md) - Multi-actor execution
- [Models](../reference/models.md) - Consumption modes and dependencies
- [Common Patterns](../reference/patterns.md) - Pattern 8: Reusable Rules
