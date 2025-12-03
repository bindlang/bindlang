# bindlang Architecture

## Module Structure

```
bindlang/
└── core/
```

## Core Module (`core/`)

| File | Purpose |
|------|---------|
| `models.py` | Data models: LatentSymbol, GateCondition, Context, BoundSymbol |
| `state.py` | Symbol state machine and lifecycle management |
| `engine.py` | BindingEngine orchestrator with composition-based managers |
| `orchestration.py` | Multi-actor execution patterns (ActorSequenceRunner) |
| `templates.py` | Symbol template validation and creation |
| `checkers.py` | Gate condition evaluation (who, when, where, state) |
| `sinks.py` | Audit sink protocol and built-in implementations |
| `export.py` | JSON/JSONL export utilities |

**Managers** (composed into BindingEngine):
| File | Purpose |
|------|---------|
| `template_manager.py` | Template registration and symbol creation |
| `audit_manager.py` | Binding attempt tracking and failure analysis |
| `export_manager.py` | Export audit trails and ledgers to files |
| `streaming_manager.py` | Sink-based audit streaming |

## Design Principles

- **Immutable** - Models frozen after creation
- **Protocol-based** - `Evaluable` for gates, `AuditSink` for storage
- **Type-safe** - Pydantic validation
- **Serializable** - JSON round-trip
- **No circular imports**
