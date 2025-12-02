# bindlang - Common Symbol Patterns

Common patterns demonstrating bindlang core primitives. All examples use standard symbol types without custom extensions.

For detailed implementations, see [examples/](../../examples/) directory.

**Advanced topics:**
- [Stress Testing](stress-testing.md) - Edge cases, scalability, and production recommendations

---

## Voting with Weights

**Use case:** Users and admins vote, but admin votes count more.

```python
from bindlang import LatentSymbol, GateCondition, Context, BindingEngine
from datetime import datetime

# Create vote symbols
vote_alice = LatentSymbol(
    id="vote_alice_promote",
    symbol_type="VOTE:promote",
    gate=GateCondition(who={"user", "admin"}),
    payload={"voter": "alice", "target": "bob", "base_weight": 1.0}
)

vote_charlie = LatentSymbol(
    id="vote_charlie_promote",
    symbol_type="VOTE:promote",
    gate=GateCondition(who={"user", "admin"}),
    payload={"voter": "charlie", "target": "bob", "base_weight": 1.0}
)

# Bind with different contexts
engine = BindingEngine()
engine.register(vote_alice)
engine.register(vote_charlie)

# Alice is admin → weight 2.0
ctx_alice = Context(
    who="admin",
    when=datetime.now(),
    where="voting_booth",
    state={"user_role": "admin", "voter_id": "alice"}
)

# Charlie is user → weight 1.0
ctx_charlie = Context(
    who="user",
    when=datetime.now(),
    where="voting_booth",
    state={"user_role": "user", "voter_id": "charlie"}
)

# Custom weight calculation
def calculate_weight(bound_symbol, context):
    base = bound_symbol.effect.get("base_weight", 1.0)
    role = context.state.get("user_role", "user")
    multiplier = 2.0 if role == "admin" else 1.0
    return base * multiplier

result_alice = engine.bind(vote_alice, ctx_alice)
result_charlie = engine.bind(vote_charlie, ctx_charlie)

# Tally votes
votes = [result_alice, result_charlie]
total_weight = sum(calculate_weight(v, ctx) for v, ctx in
                   [(result_alice, ctx_alice), (result_charlie, ctx_charlie)])
print(f"Total vote weight: {total_weight}")  # 3.0 (2.0 + 1.0)
```

---

## Witness Pattern (Quorum)

**Use case:** Critical action requires 2 witnesses to approve.

```python
from bindlang import LatentSymbol, GateCondition, Context, BindingEngine

# Create witness symbols
witness1 = LatentSymbol(
    id="witness_alice_delete",
    symbol_type="WITNESS:approve",
    gate=GateCondition(who={"moderator", "admin"}),
    payload={"witness_id": "alice", "action": "delete_project_x"}
)

witness2 = LatentSymbol(
    id="witness_bob_delete",
    symbol_type="WITNESS:approve",
    gate=GateCondition(who={"moderator", "admin"}),
    payload={"witness_id": "bob", "action": "delete_project_x"}
)

# The actual delete action - depends on witnesses
delete_action = LatentSymbol(
    id="delete_project_x",
    symbol_type="EVENT:delete",
    gate=GateCondition(who={"admin"}),
    payload={"project": "x", "danger_level": "high"},
    depends_on=["witness_alice_delete", "witness_bob_delete"]  # Requires BOTH
)

engine = BindingEngine()
for symbol in [witness1, witness2, delete_action]:
    engine.register(symbol)

# Witnesses approve
ctx_alice = Context(who="moderator", when=datetime.now(), where="review", state={"witness": "alice"})
ctx_bob = Context(who="moderator", when=datetime.now(), where="review", state={"witness": "bob"})

engine.bind(witness1, ctx_alice)
engine.bind(witness2, ctx_bob)

# Now delete can proceed (both witnesses activated)
ctx_admin = Context(who="admin", when=datetime.now(), where="production", state={})
result = engine.bind(delete_action, ctx_admin)

if result:
    print("Delete approved by quorum")
else:
    print("Quorum not met")
```

---

## Temporal Conditions

**Use case:** Feature unlocks after a specific date.

```python
from bindlang import LatentSymbol, GateCondition, Context
from datetime import datetime

# Feature available after launch date
new_feature = LatentSymbol(
    id="beta_feature",
    symbol_type="FEATURE:beta",
    gate=GateCondition(when="after:2025-01-15"),
    payload={"feature": "advanced_editor"}
)

# Before launch
ctx_before = Context(
    who="user",
    when=datetime(2025, 1, 10),
    where="app",
    state={}
)

# After launch
ctx_after = Context(
    who="user",
    when=datetime(2025, 1, 20),
    where="app",
    state={}
)

engine = BindingEngine()
engine.register(new_feature)

result_before = engine.bind(new_feature, ctx_before)
result_after = engine.bind(new_feature, ctx_after)

print(f"Before launch: {result_before is not None}")  # False
print(f"After launch: {result_after is not None}")    # True
```

---

## Workflow Approval Chain

**Use case:** Document must be approved by manager, then director, then published.

```python
from bindlang import LatentSymbol, GateCondition, Context, BindingEngine

# Step 1: Manager approval
manager_approval = LatentSymbol(
    id="approve_manager",
    symbol_type="APPROVAL:manager",
    gate=GateCondition(who={"manager"}),
    payload={"approver": "manager", "document": "doc_123"}
)

# Step 2: Director approval (depends on manager)
director_approval = LatentSymbol(
    id="approve_director",
    symbol_type="APPROVAL:director",
    gate=GateCondition(who={"director"}),
    payload={"approver": "director", "document": "doc_123"},
    depends_on=["approve_manager"]
)

# Step 3: Publish (depends on director)
publish = LatentSymbol(
    id="publish_doc",
    symbol_type="EVENT:publish",
    gate=GateCondition(who={"system"}),
    payload={"document": "doc_123", "status": "published"},
    depends_on=["approve_director"]
)

engine = BindingEngine()
for symbol in [manager_approval, director_approval, publish]:
    engine.register(symbol)

# Manager approves
ctx_manager = Context(who="manager", when=datetime.now(), where="review", state={})
engine.bind(manager_approval, ctx_manager)

# Director approves
ctx_director = Context(who="director", when=datetime.now(), where="review", state={})
engine.bind(director_approval, ctx_director)

# System publishes
ctx_system = Context(who="system", when=datetime.now(), where="pipeline", state={})
result = engine.bind(publish, ctx_system)

if result:
    print("Document published after full approval chain")
```

---

## Narrative Compression

**Use case:** Compress story context by activating only relevant symbols for edits.

See `narrative_compression_test.py` for full example.

**Pattern:**

```python
# Extract story elements as symbols
character_state = LatentSymbol(
    id="char_anna_beach",
    symbol_type="CHARSTATE:emotional",
    gate=GateCondition(
        where={"paragraph_1", "beach_scene"},
        state={"character": "Anna"}
    ),
    payload={
        "character": "Anna",
        "location": "beach",
        "emotion": "contemplative"
    }
)

# Edit paragraph 1 → only paragraph_1 symbols activate
ctx_edit = Context(
    who="editor",
    when=datetime.now(),
    where="paragraph_1",
    state={"character": "Anna"}
)

# Result: 2-3 symbols activated instead of 500 (5-10x compression)
```

---

## Multi-Tenant Policies

**Use case:** Same action, different rules per tenant.

```python
# Delete project symbol (same for all tenants)
delete_project = LatentSymbol(
    id="delete_project",
    symbol_type="EVENT:delete",
    gate=GateCondition(who={"admin", "owner"}),
    payload={"action": "delete"}
)

# Tenant A (permissive)
ctx_tenant_a = Context(
    who="admin",
    when=datetime.now(),
    where="tenant_a",
    state={"policy": "permissive"}
)

# Tenant B (strict - requires witnesses)
ctx_tenant_b = Context(
    who="admin",
    when=datetime.now(),
    where="tenant_b",
    state={"policy": "strict", "witnesses_count": 2}
)

# Custom policy enforcement
def can_delete(context):
    if context.where == "tenant_a":
        return True  # Permissive
    elif context.where == "tenant_b":
        # Check witness count
        return context.state.get("witnesses_count", 0) >= 2
    return False

# Enforce policy
if can_delete(ctx_tenant_a):
    print("Tenant A: Delete allowed")

if can_delete(ctx_tenant_b):
    print("Tenant B: Delete allowed (witnesses met)")
```
