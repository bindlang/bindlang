# bindlang Core Architecture

## Theoretical Foundation → Implementation

```mermaid
graph TB
    subgraph "DSBL Theory - The Fourth Semantic Dimension"
        Theory[Latent/Bound Semantics<br/>Meaning that waits vs Meaning fixed by context]
        Analogy[Sealed Ballot Analogy<br/>Intent exists but outcome pending]
        Principle[Defer WHAT gets determined<br/>not WHEN it executes]

        Theory --> Analogy
        Theory --> Principle
    end

    subgraph "bindlang Implementation"
        LatentSymbol[LatentSymbol<br/>Meaning that waits]
        BoundSymbol[BoundSymbol<br/>Meaning fixed by context]
        Transition[Binding Process<br/>Latent → Bound]

        LatentSymbol --> Transition
        Transition --> BoundSymbol
    end

    Theory -.maps to.-> LatentSymbol
    Principle -.maps to.-> Transition
    Analogy -.maps to.-> BoundSymbol

    style Theory fill:#E3F2FD
    style LatentSymbol fill:#4CAF50
    style BoundSymbol fill:#FF9800
    style Transition fill:#2196F3
```

## Core Architecture - System Overview

```mermaid
graph TB
    subgraph "Core Data Models"
        direction LR

        LS[LatentSymbol<br/>━━━━━━━━━<br/>id: str<br/>symbol_type: str<br/>payload: Dict<br/>gate: GateCondition<br/>depends_on: List]

        GC[GateCondition<br/>━━━━━━━━━<br/>who: Set<br/>where: Set<br/>when: Temporal<br/>state: Dict]

        BS[BoundSymbol<br/>━━━━━━━━━<br/>symbol_id: str<br/>symbol_type: str<br/>effect: Dict<br/>weight: float<br/>bound_at: datetime]

        CTX[Context<br/>━━━━━━━━━<br/>who: str<br/>when: datetime<br/>where: str<br/>state: Dict]

        LS -.has.-> GC
    end

    subgraph "Binding Engine"
        direction TB
        Engine[BindingEngine]
        Registry[symbol_registry<br/>Dict: id → LatentSymbol]
        DepGraph[dependency_graph<br/>topological ordering]
        Audit[audit_trail<br/>BindingAttempt records]

        Engine --> Registry
        Engine --> DepGraph
        Engine --> Audit
    end

    subgraph "Checker System"
        direction LR
        WhoChecker[WhoChecker<br/>Set matching]
        WhereChecker[WhereChecker<br/>Set matching]
        WhenChecker[WhenChecker<br/>Temporal eval]
        StateChecker[StateChecker<br/>Dict matching]
    end

    %% Connections
    LS --> Registry
    CTX --> Engine
    Engine --> WhoChecker
    Engine --> WhereChecker
    Engine --> WhenChecker
    Engine --> StateChecker
    Engine -.creates.-> BS

    style LS fill:#C8E6C9
    style BS fill:#FFCC80
    style CTX fill:#90CAF9
    style Engine fill:#CE93D8
```

## Design Decision Map

```mermaid
graph LR
    subgraph "Key Design Decisions"
        D1[Decision 1:<br/>Immutable Context]
        D2[Decision 2:<br/>AND Logic Gates]
        D3[Decision 3:<br/>Symbol ≠ Instance]
        D4[Decision 4:<br/>Dependency Graph]
        D5[Decision 5:<br/>Pydantic Models]
        D6[Decision 6:<br/>Checker Separation]
    end

    subgraph "Rationale & Benefits"
        R1[Prevents race conditions<br/>Reproducible binding<br/>Audit clarity]

        R2[Conservative activation<br/>Explicit requirements<br/>Predictable behavior]

        R3[One latent → many bounds<br/>Reusability<br/>Immutable contracts]

        R4[Circular detection<br/>Cascade activation<br/>DFS-based validation]

        R5[Type safety<br/>Validation<br/>IDE support<br/>Serialization]

        R6[Single Responsibility<br/>Extensible<br/>Testable]
    end

    D1 --> R1
    D2 --> R2
    D3 --> R3
    D4 --> R4
    D5 --> R5
    D6 --> R6

    style D1 fill:#BBDEFB
    style D2 fill:#C5CAE9
    style D3 fill:#D1C4E9
    style D4 fill:#E1BEE7
    style D5 fill:#F8BBD0
    style D6 fill:#FFCCBC
```

## Binding Process - Detailed Flow

```mermaid
sequenceDiagram
    participant User
    participant Engine
    participant Registry
    participant Checker
    participant DepGraph
    participant Audit

    %% Registration Phase
    User->>Engine: register(LatentSymbol)
    Engine->>Registry: store symbol
    Engine->>DepGraph: add node + edges
    DepGraph->>DepGraph: check for cycles
    alt Cycle detected
        DepGraph-->>Engine: CircularDependencyError
        Engine-->>User: Error
    else No cycle
        Engine-->>User: Symbol registered
    end

    %% Binding Phase
    User->>Engine: bind_all_registered(Context)
    Engine->>Registry: get all symbols

    loop For each symbol
        Engine->>Engine: check dependencies
        alt Dependencies not satisfied
            Engine->>Engine: skip (remains LATENT, no audit entry)
        else Dependencies satisfied
            Engine->>Checker: evaluate_gate(symbol.gate, context)

            Checker->>Checker: WhoChecker.check()
            Checker->>Checker: WhereChecker.check()
            Checker->>Checker: WhenChecker.check()
            Checker->>Checker: StateChecker.check()

            alt All checks pass (AND logic)
                Checker-->>Engine: PASS
                Engine->>Engine: create BoundSymbol
                Engine->>Audit: record success
                Engine->>Engine: add to results
            else Any check fails
                Checker-->>Engine: FAIL(reason)
                Engine->>Audit: record failure (gate check)
            end
        end
    end

    Engine-->>User: List[BoundSymbol]
```

## The Gate System - Context Matching

```mermaid
graph TB
    subgraph "GateCondition - The Contract"
        Who["who: Set<br/>WHO can activate?<br/>Example: alice, bob"]
        Where["where: Set<br/>WHERE can it activate?<br/>Example: beach, forest"]
        When["when: Temporal<br/>WHEN can it activate?<br/>Example: after 2024-01-01"]
        State["state: Dict<br/>WHAT state required?<br/>Example: level=5"]

        Logic[Combine with AND<br/>ALL must match]

        Who --> Logic
        Where --> Logic
        When --> Logic
        State --> Logic
    end

    subgraph "Context - The Reality"
        CWho["who: str<br/>WHO is acting<br/>Example: alice"]
        CWhere["where: str<br/>WHERE is it<br/>Example: beach"]
        CWhen["when: datetime<br/>WHEN is it<br/>Example: 2024-03-15"]
        CState["state: Dict<br/>WHAT is state<br/>Example: level=7"]
    end

    subgraph "Checker Logic"
        WhoCheck{who in gate.who?}
        WhereCheck{where in gate.where?}
        WhenCheck{when satisfies gate.when?}
        StateCheck{All gate.state keys match?}

        Final{ALL pass?}
    end

    CWho --> WhoCheck
    CWhere --> WhereCheck
    CWhen --> WhenCheck
    CState --> StateCheck

    Who -.required by.-> WhoCheck
    Where -.required by.-> WhereCheck
    When -.required by.-> WhenCheck
    State -.required by.-> StateCheck

    WhoCheck --> Final
    WhereCheck --> Final
    WhenCheck --> Final
    StateCheck --> Final

    Final -->|YES| Bind[Create BoundSymbol]
    Final -->|NO| Skip[Remains Latent<br/>Record in audit]

    style Who fill:#E8F5E9
    style Where fill:#E3F2FD
    style When fill:#FFF3E0
    style State fill:#FCE4EC
    style Bind fill:#C8E6C9
    style Skip fill:#FFCDD2
```

## Dependency System - Cascade Activation

```mermaid
graph TB
    subgraph "Dependency Chain Example"
        A[Symbol A<br/>No dependencies<br/>Gate: who=alice]
        B[Symbol B<br/>depends_on: A<br/>Gate: where=beach]
        C[Symbol C<br/>depends_on: B<br/>Gate: state.ready=true]
        D[Symbol D<br/>depends_on: B and C<br/>Gate: None]

        A -->|must bind first| B
        B -->|must bind first| C
        B -->|must bind first| D
        C -->|must bind first| D
    end

    subgraph "Dependency Graph"
        direction LR
        NodeA((A))
        NodeB((B))
        NodeC((C))
        NodeD((D))

        NodeA -.edge.-> NodeB
        NodeB -.edge.-> NodeC
        NodeB -.edge.-> NodeD
        NodeC -.edge.-> NodeD
    end

    subgraph "Binding Rounds"
        R1[Round 1:<br/>Context: who=alice<br/>Result: A binds]
        R2[Round 2:<br/>Context: where=beach<br/>Result: B binds<br/>A already bound]
        R3[Round 3:<br/>Context: state.ready=true<br/>Result: C binds<br/>B already bound]
        R4[Round 4:<br/>Context: any<br/>Result: D binds<br/>B,C already bound]

        R1 --> R2
        R2 --> R3
        R3 --> R4
    end

    subgraph "Circular Detection"
        X[Symbol X<br/>depends_on: Y]
        Y[Symbol Y<br/>depends_on: Z]
        Z[Symbol Z<br/>depends_on: X]

        X --> Y
        Y --> Z
        Z --> X

        Error[CircularDependencyError<br/>Cycle: X → Y → Z → X]

        Z -.detected.-> Error
    end

    style A fill:#C8E6C9
    style B fill:#A5D6A7
    style C fill:#81C784
    style D fill:#66BB6A
    style Error fill:#EF5350
```

## Multi-Actor Orchestration - ActorSequenceRunner

```mermaid
sequenceDiagram
    participant User
    participant Runner as ActorSequenceRunner
    participant Engine as BindingEngine
    participant State

    User->>Runner: run_actor_sequence(actor_contexts, initial_state)
    Runner->>State: Initialize shared state

    loop For each actor_context
        Note over Runner: Actor A perspective

        Runner->>Runner: Build Context(actor, shared_state)
        Runner->>Engine: bind_all_registered(context)
        Engine-->>Runner: activated symbols

        loop For each activated symbol
            alt Symbol has state_mutation in payload
                Runner->>State: Apply mutation to shared state
                Note over State: State evolves:<br/>lab_open=true
            end
        end

        Note over Runner: Actor B perspective (uses updated state)

        Runner->>Runner: Build Context(actor_b, shared_state)
        Runner->>Engine: bind_all_registered(context)
        Engine-->>Runner: new symbols activate

        Note over Runner: Witness semantics:<br/>Each actor observes from their perspective
    end

    Runner-->>User: (all_bound_symbols, final_state)
```

**Key Properties:**
- **Sequential perspectives**: Each actor binds in order
- **Shared state**: Mutations from one actor affect next actor's context
- **Witness semantics**: `who=None` gates activate for any actor
- **State accumulation**: Final state reflects all mutations

## Audit Trail - Tracking Binding Attempts

```mermaid
graph TB
    subgraph "BindingAttempt Model"
        BA[BindingAttempt<br/>━━━━━━━━━<br/>symbol_id: str<br/>success: bool<br/>attempt_timestamp: datetime<br/>context_snapshot: Dict<br/>failure_reasons: List[FailureReason]]

        FR[FailureReason<br/>━━━━━━━━━<br/>category: str<br/>message: str<br/>gate_dimension: str]

        BA --> FR
    end

    subgraph "AuditSink System"
        Sink[AuditSink<br/>Abstract base class]

        JSONSink[JSONLFileSink<br/>Streaming JSONL output]
        ConsoleSink[ConsoleSink<br/>stdout logging]
        CustomSink[Custom implementations<br/>SQLite, in-memory, etc]

        JSONSink -.implements.-> Sink
        ConsoleSink -.implements.-> Sink
        CustomSink -.implements.-> Sink
    end

    subgraph "Integration with Engine"
        Engine[BindingEngine<br/>audit_sink: AuditSink]

        Success[On binding success:<br/>Record attempt with success=True]
        Failure[On gate failure:<br/>Record attempt with reasons]

        Engine --> Success
        Engine --> Failure

        Success --> Sink
        Failure --> Sink
    end

    subgraph "Failure Categories"
        Cat1[DEPENDENCY_NOT_MET<br/>Required symbols not bound]
        Cat2[GATE_WHO_FAILED<br/>who not in gate.who]
        Cat3[GATE_WHERE_FAILED<br/>where not in gate.where]
        Cat4[GATE_WHEN_FAILED<br/>Temporal condition not met]
        Cat5[GATE_STATE_FAILED<br/>State key mismatch]
    end

    FR -.category.-> Cat1
    FR -.category.-> Cat2
    FR -.category.-> Cat3
    FR -.category.-> Cat4
    FR -.category.-> Cat5

    style BA fill:#E1BEE7
    style FR fill:#F48FB1
    style Sink fill:#90CAF9
    style Engine fill:#CE93D8
```

**Usage:**
- Debug failed activations: Check `failure_reasons` for specific gate dimension
- Performance analysis: Count attempts per symbol over time
- Compliance audit: Track who attempted what, when, and result
- Custom sinks: Extend `AuditSink` for database, metrics, or logging integration

## Summary: Theory → Design → Implementation

| Theoretical Concept | Design Decision | Implementation |
|---------------------|-----------------|----------------|
| **Latent semantics** | Symbols carry potential meaning | `LatentSymbol` with payload |
| **Context-dependent activation** | Gates define activation conditions | `GateCondition` + Checker system |
| **Bound semantics** | Context fixes meaning | `BoundSymbol` with effect |
| **Immutability** | Contracts don't change | Pydantic frozen models |
| **Explicit causality** | Track what activated why | Audit trail + context snapshot |
| **Dependency tracking** | Some symbols need others first | DFS-based dependency graph |
| **Multi-actor coordination** | Sequential perspectives with shared state | ActorSequenceRunner |
| **Separation of concerns** | Checkers are independent | One checker per dimension |
| **Type safety** | Validate contracts | Pydantic + template validation |

**Core insight:** The "Latent/Bound" semantic dimension is implemented through:
1. **LatentSymbol** = Semantic potential (what COULD happen)
2. **GateCondition** = Activation contract (WHEN it happens)
3. **Context** = Runtime reality (what IS)
4. **Checker system** = Evaluation logic (does reality match contract?)
5. **BoundSymbol** = Fixed meaning (what DID happen)

This maps the theoretical "sealed ballot" analogy directly into executable code.

## See Also

- [Template System](template-system.md) - Reusable symbol blueprints
- [Advanced Patterns](advanced-patterns.md) - Composition and portability examples
- [Reference Documentation](../reference/index.md) - API reference
