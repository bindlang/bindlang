# Advanced Patterns - Composition and Portability

## State Evolution - Multi-Round Binding

```mermaid
sequenceDiagram
    participant User
    participant Engine
    participant Context
    participant Evolve

    User->>Engine: bind_with_state_evolution(context, evolve_fn, max_iterations)

    loop Each iteration (max 10)
        Engine->>Engine: bind_all_registered(context)
        Note over Engine: Symbols activate based on current context

        Engine->>Evolve: evolve_fn(engine, context, iteration)
        Note over Evolve: User function modifies context based on activations
        Evolve-->>Engine: new_context

        Context->>Context: Transform state
        Note over Context: Context evolves: state updates, new who/where

        alt No new activations
            Engine-->>User: Converged early
        end
    end

    Engine-->>User: Final results + all contexts
```

**Pattern:** Context transformation between binding rounds enables reactive systems.

**Use cases:**
- Laboratory scenario: Door opens → researchers enter → experiments begin
- Approval chains: Manager approves → director review unlocked → publication enabled
- Game state: Player moves → enemies react → loot spawns

**Key insight:** State mutations in symbol payloads drive context evolution without manual orchestration.

---

## Complete Example - Theory to Practice

```mermaid
graph TB
    subgraph "1. Theory: Latent Meaning"
        T1["If Anna is at beach, she feels brave<br/>Intent exists<br/>Outcome pending"]
    end

    subgraph "2. Implementation: LatentSymbol"
        L1["LatentSymbol<br/>id: anna_brave<br/>type: CHARSTATE:brave<br/>payload: character=Anna, emotion=brave<br/>gate: where=beach"]
    end

    subgraph "3. Context Arrives"
        C1["Context<br/>who: narrator<br/>when: 2024-03-15<br/>where: beach<br/>state: chapter=5"]
    end

    subgraph "4. Gate Evaluation"
        E1["WhereChecker<br/>beach in gate.where?<br/>PASS"]
    end

    subgraph "5. Bound Meaning"
        B1["BoundSymbol<br/>symbol_id: anna_brave<br/>effect: character=Anna, emotion=brave<br/>bound_at: 2024-03-15T14:30<br/>context_snapshot: where=beach"]
    end

    subgraph "6. Effect Delivered"
        F1["Anna IS brave at beach<br/>Meaning fixed by context<br/>Outcome determined"]
    end

    T1 --> L1
    L1 --> E1
    C1 --> E1
    E1 --> B1
    B1 --> F1

    style T1 fill:#E8F5E9
    style L1 fill:#C8E6C9
    style C1 fill:#90CAF9
    style E1 fill:#F48FB1
    style B1 fill:#FFCC80
    style F1 fill:#FFE082
```

**Demonstrates:** End-to-end flow from theoretical concept (latent meaning) to concrete execution (bound symbol with fixed effect).

---

## Portable Contracts - Cross-Component Composition

```mermaid
graph TB
    subgraph "Component A: Story Editor"
        A1["Create Symbol:<br/>CHARSTATE:brave<br/>gate: where=beach"]
        A2["Create Symbol:<br/>PLOT:dragon_defeat<br/>gate: depends_on=char_brave"]
        A3["Serialize to JSON"]

        A1 --> A2
        A2 --> A3
    end

    subgraph "Transport Layer"
        JSON["Portable JSON<br/>━━━━━━━━━<br/>No runtime context<br/>No execution state<br/>Pure semantic contract"]

        A3 --> JSON
    end

    subgraph "Component B: Game Engine"
        B1["Deserialize from JSON"]
        B2["Register in local engine"]
        B3["Bind with game context:<br/>player_location=beach"]
        B4["Symbol activates<br/>Dragon defeated"]

        JSON --> B1
        B1 --> B2
        B2 --> B3
        B3 --> B4
    end

    subgraph "Component C: Analytics"
        C1["Deserialize same JSON"]
        C2["Bind with analytics context:<br/>chapter=5, act=finale"]
        C3["Symbol activates<br/>Story climax detected"]

        JSON --> C1
        C1 --> C2
        C2 --> C3
    end

    Note1["Same symbol definition<br/>Different contexts<br/>Different meanings<br/>━━━━━━━━━<br/>This is PORTABILITY"]

    style JSON fill:#FFE082
    style B4 fill:#C8E6C9
    style C3 fill:#90CAF9
    style Note1 fill:#FFCCBC
```

**Pattern:** Symbols serialize to JSON and activate differently across components.

**Properties:**
- **Decoupled meaning:** Symbol definition independent of execution environment
- **Context-dependent activation:** Same symbol, different outcomes based on local context
- **Zero runtime coupling:** Components don't share state, only symbol contracts

**Use cases:**
- Editor creates symbols → Game engine executes them
- ML model produces symbols → Analytics consumes them
- Multi-agent system: Agents share symbol pool, bind from individual perspectives

---

## Multi-Agent Witness Quorum

```mermaid
graph LR
    subgraph "Agent Alice"
        A_Create["Creates:<br/>WITNESS:alice_saw<br/>payload: event=theft<br/>gate: who=alice"]
        A_Sign["Signs with:<br/>timestamp + hash"]
    end

    subgraph "Shared Symbol Pool"
        Pool["Symbol Registry<br/>━━━━━━━━━<br/>WITNESS:alice_saw<br/>WITNESS:bob_saw<br/>WITNESS:charlie_saw<br/>━━━━━━━━━<br/>All dormant"]
    end

    subgraph "Agent Bob"
        B_Create["Creates:<br/>WITNESS:bob_saw<br/>payload: event=theft<br/>gate: who=bob"]
        B_Sign["Signs with:<br/>timestamp + hash"]
    end

    subgraph "Agent Charlie"
        C_Create["Creates:<br/>WITNESS:charlie_saw<br/>payload: event=theft<br/>gate: who=charlie"]
        C_Sign["Signs with:<br/>timestamp + hash"]
    end

    subgraph "Quorum Detector"
        Q1["Bind with context:<br/>event=theft"]
        Q2["3 witnesses activate"]
        Q3["QUORUM:achieved<br/>payload: confidence=0.95<br/>depends_on: alice, bob, charlie"]
    end

    subgraph "Decision System"
        D1["Bind quorum symbol<br/>with context:<br/>requires_approval=true"]
        D2["APPROVAL:granted<br/>Automated decision<br/>based on quorum"]
    end

    A_Create --> A_Sign
    B_Create --> B_Sign
    C_Create --> C_Sign

    A_Sign --> Pool
    B_Sign --> Pool
    C_Sign --> Pool

    Pool --> Q1
    Q1 --> Q2
    Q2 --> Q3

    Q3 --> D1
    D1 --> D2

    Note3["Symbols created by different agents<br/>Combined to create emergent meaning<br/>No agent knew about quorum logic<br/>━━━━━━━━━<br/>This is COMPOSABILITY"]

    style Pool fill:#E1BEE7
    style Q3 fill:#CE93D8
    style D2 fill:#AB47BC
    style Note3 fill:#FFCCBC
```

**Pattern:** Independent agents contribute symbols that compose into higher-order meaning.

**Key properties:**
- **Emergent semantics:** Quorum meaning emerges from individual witness symbols
- **Decentralized creation:** No central coordinator required
- **Dependency-based composition:** QUORUM symbol depends on witness symbols
- **Automated decision:** Approval granted when quorum threshold met

**Use cases:**
- Multi-signature approval workflows
- Distributed consensus systems
- Byzantine fault tolerance (witness verification)
- Collaborative decision-making

---

## Dependency Cascade Example

**Scenario:** Document publication requires manager approval, then director approval, then legal review.

```python
from bindlang import LatentSymbol, GateCondition, Context, BindingEngine
from datetime import datetime

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

# Step 3: Legal review (depends on director)
legal_review = LatentSymbol(
    id="legal_review",
    symbol_type="REVIEW:legal",
    gate=GateCondition(who={"legal"}),
    payload={"reviewer": "legal", "document": "doc_123"},
    depends_on=["approve_director"]
)

# Step 4: Publish (depends on legal)
publish = LatentSymbol(
    id="publish_doc",
    symbol_type="EVENT:publish",
    gate=GateCondition(who={"system"}),
    payload={"document": "doc_123", "status": "published"},
    depends_on=["legal_review"]
)

engine = BindingEngine()
for symbol in [manager_approval, director_approval, legal_review, publish]:
    engine.register(symbol)

# Round 1: Manager approves
ctx_manager = Context(who="manager", when=datetime.now(), where="review", state={})
engine.bind(manager_approval, ctx_manager)

# Round 2: Director approves (now unblocked)
ctx_director = Context(who="director", when=datetime.now(), where="review", state={})
engine.bind(director_approval, ctx_director)

# Round 3: Legal reviews (now unblocked)
ctx_legal = Context(who="legal", when=datetime.now(), where="review", state={})
engine.bind(legal_review, ctx_legal)

# Round 4: System publishes (all dependencies met)
ctx_system = Context(who="system", when=datetime.now(), where="pipeline", state={})
result = engine.bind(publish, ctx_system)

if result:
    print("Document published after full approval chain")
```

**Result:** Each step activates only when dependencies are satisfied, creating a cascading approval workflow.

---

## Combining Patterns

**State Evolution + Dependencies + Multi-Actor:**

```python
from bindlang import ActorSequenceRunner, BindingEngine, LatentSymbol, GateCondition

engine = BindingEngine()

# Symbol 1: Lab opens (witness gate - activates for any actor)
lab_opens = LatentSymbol(
    id="lab_opens",
    symbol_type="EVENT:open",
    gate=GateCondition(who=None, where={"lab"}),
    payload={"state_mutation": {"lab_open": True}}
)

# Symbol 2: Researcher arrives (depends on lab being open)
researcher_arrives = LatentSymbol(
    id="researcher_arrives",
    symbol_type="ACTION:arrive",
    gate=GateCondition(who={"researcher_a"}, state={"lab_open": True}),
    payload={"state_mutation": {"researcher_a_present": True}}
)

# Symbol 3: Experiment starts (depends on researcher presence)
experiment_starts = LatentSymbol(
    id="experiment_starts",
    symbol_type="EVENT:experiment",
    gate=GateCondition(state={"researcher_a_present": True}),
    payload={"experiment": "alpha", "status": "running"}
)

engine.register(lab_opens)
engine.register(researcher_arrives)
engine.register(experiment_starts)

# Run multi-actor sequence
runner = ActorSequenceRunner(engine)
actor_contexts = [
    {"who": None, "where": "lab"},  # System opens lab
    {"who": "researcher_a", "where": "lab"},  # Researcher arrives
    {"who": "supervisor", "where": "lab"}  # Supervisor observes
]

bound, final_state = runner.run_actor_sequence(actor_contexts, initial_state={})

print(f"Final state: {final_state}")
# Output: {'lab_open': True, 'researcher_a_present': True}
```

**Combines:**
- Witness gates (`who=None`)
- State mutations (lab_open, researcher_a_present)
- Dependencies (researcher → experiment)
- Multi-actor orchestration (system, researcher, supervisor)

---

## See Also

- [Core Architecture](core-architecture.md) - Fundamental system design
- [Template System](template-system.md) - Reusable symbol blueprints
- [Orchestration Reference](../reference/orchestration.md) - ActorSequenceRunner API
- [Common Patterns](../reference/patterns.md) - Pattern catalog
- [State Mutations Guide](../guides/state-mutations.md) - State evolution mechanics
