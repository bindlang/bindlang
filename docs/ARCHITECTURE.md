# bindlang Architecture

**Version**: 0.1.0

---

## Module Structure

```
bindlang/
└── core/           # Core abstractions (Pydantic only)
```

---

## Core Module (`core/`)

**Foundation:** Zero external dependencies except Pydantic.

| File | Purpose |
|------|---------|
| `models.py` | Data models: LatentSymbol, Gate, Context, BoundSymbol |
| `state.py` | Symbol state machine and lifecycle management |
| `engine.py` | BindingEngine orchestrator with composition-based managers |
| `orchestration.py` | Multi-actor execution patterns (ActorSequenceRunner) |
| `templates.py` | Symbol template validation and creation |
| `checkers.py` | Gate condition evaluation (who, when, where, state, etc.) |
| `sinks.py` | Pluggable audit sink architecture (Protocol + built-in sinks) |
| `export.py` | JSON/JSONL export utilities |

**Managers** (composed into BindingEngine):
- `template_manager.py` - Template registration and symbol creation
- `audit_manager.py` - Binding attempt tracking and failure analysis
- `export_manager.py` - Export audit trails and ledgers to files
- `streaming_manager.py` - Pluggable sink-based audit streaming

---

## Design Principles

- **Immutable** - All models frozen after creation
- **Protocol-based** - `Evaluable` protocol for extensible gates, `AuditSink` for pluggable storage
- **Type-safe** - Pydantic validation throughout
- **Serializable** - JSON round-trip support
- **No circular dependencies** - Clean layered architecture
- **Mechanism not policy** - Core provides hooks, users choose implementations (e.g., sinks)

---

## Data Flow

```
LatentSymbol created
    ↓
Registered with BindingEngine (CREATED → DORMANT)
    ↓
Context provided
    ↓
engine.bind() evaluates gate conditions via checkers
    ↓
Success: DORMANT → ACTIVATED, returns BoundSymbol
Failure: Records FailureReason to audit trail
```

**Two tracking systems:**
- `engine.ledger` - State transition history
- `engine.audit.trail` - Detailed binding attempts with failure reasons

---

## Documentation

**Getting Started:**
- [Installation](reference/installation.md) - Install bindlang locally or from PyPI
- [Quickstart](reference/quickstart.md) - Get started in 5 minutes

**Core API:**
- [Models Reference](reference/models.md) - Data structures and validation
- [Engine Reference](reference/engine.md) - BindingEngine API and managers
- [Orchestration](reference/orchestration.md) - Multi-actor execution patterns
- [Templates](reference/templates.md) - Symbol validation and reusable blueprints
- [Audit Trail](reference/audit-trail.md) - Debugging with structured failure reasons

**Practical Usage:**
- [Patterns](reference/patterns.md) - Common usage patterns
- [Serialization](reference/serialization.md) - JSON export/import
- [Debugging](reference/debugging.md) - Audit trail and diagnostics

**For theory:**
- [FOUNDATION.md](theory/FOUNDATION.md) - Theoretical foundation
- [Theory site](https://dsbl.dev/latentbound.html) - Deferred semantic binding concepts

---

## Extensibility

Users can extend bindlang through:
- Custom gates implementing `Evaluable` protocol
- Custom audit sinks implementing `AuditSink` protocol
- Subclassing BindingEngine for custom weight calculation

See [Engine Reference](reference/engine.md) for details.

---
