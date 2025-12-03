# bindlang Core Architecture

## Core Concept

bindlang separates **what could happen** from **what does happen**.

Instead of imperative orchestration ("do X, then Y, wait for Z"), bindlang uses declarative contracts. Symbols define their activation conditions and remain latent until context satisfies them:

```mermaid
graph LR
    subgraph "bindlang Flow"
        LS[LatentSymbol<br/>Potential meaning]
        Gate[Gate Check<br/>Context evaluation]
        BS[BoundSymbol<br/>Fixed meaning]

        LS --> Gate
        Gate -->|pass| BS
    end

    style LS fill:#4CAF50,color:#000
    style Gate fill:#2196F3,color:#000
    style BS fill:#FF9800,color:#000
```

Symbols carry intent that remains dormant until context activates them. See [Foundation](../theory/FOUNDATION.md) for theoretical background.

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

    style LS fill:#C8E6C9,color:#000
    style BS fill:#FFCC80,color:#000
    style CTX fill:#90CAF9,color:#000
    style Engine fill:#CE93D8,color:#000
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

    style A fill:#C8E6C9,color:#000
    style B fill:#A5D6A7,color:#000
    style C fill:#81C784,color:#000
    style D fill:#66BB6A,color:#000
    style Error fill:#EF5350,color:#000
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

Each actor binds in order. State mutations affect subsequent actors. `who=None` gates activate for any actor.

## Audit Trail - Tracking Binding Attempts

```mermaid
graph TB
    subgraph "BindingAttempt Model"
        BA[BindingAttempt<br/>━━━━━━━━━<br/>symbol_id: str<br/>success: bool<br/>attempt_timestamp: datetime<br/>context_snapshot: Dict<br/>failure_reasons: List]

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

    style BA fill:#E1BEE7,color:#000
    style FR fill:#F48FB1,color:#000
    style Sink fill:#90CAF9,color:#000
    style Engine fill:#CE93D8,color:#000
```

Check `failure_reasons` for debugging. Extend `AuditSink` for custom storage.

## See Also

- [Template System](template-system.md)
- [Advanced Patterns](advanced-patterns.md)
- [Reference Documentation](../reference/index.md)
