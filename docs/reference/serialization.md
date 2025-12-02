# JSON Serialization

[Back to Reference](index.md)

All core models support JSON round-trip via Pydantic.

---

## LatentSymbol

```python
from bindlang import LatentSymbol, GateCondition

symbol = LatentSymbol(
    id="vote_promote",
    symbol_type="VOTE:promote",
    gate=GateCondition(who={"admin"}),
    payload={"target": "alice"}
)

# To JSON string
json_str = symbol.model_dump_json()

# From JSON string
symbol = LatentSymbol.model_validate_json(json_str)

# To Python dict
data = symbol.model_dump()

# From Python dict
symbol = LatentSymbol.model_validate(data)
```

---

## Context

```python
from bindlang import Context
from datetime import datetime

context = Context(
    who="admin",
    when=datetime.now(),
    where="production",
    state={"verified": True}
)

# To JSON
json_str = context.model_dump_json()

# From JSON
context = Context.model_validate_json(json_str)
```

**Note:** `when` field is serialized as ISO datetime string

---

## BoundSymbol

```python
# BoundSymbol is created by engine.bind()
bound = engine.bind(symbol, context)

# To JSON
json_str = bound.model_dump_json()

# From JSON
from bindlang.core.models import BoundSymbol
bound = BoundSymbol.model_validate_json(json_str)
```

---

## Export/Import Full Registry

Save all registered symbols to file:

```python
from bindlang import BindingEngine
import json

engine = BindingEngine()

# ... register symbols ...

# Export all symbols to JSON
symbols_data = [s.model_dump() for s in engine.symbol_registry.values()]

with open("symbols.json", "w") as f:
    json.dump(symbols_data, f, indent=2)

# Import symbols from JSON
with open("symbols.json") as f:
    symbols_data = json.load(f)

from bindlang import LatentSymbol
for data in symbols_data:
    symbol = LatentSymbol.model_validate(data)
    engine.register(symbol)
```

---

## Export with Context

Save symbols along with context for reproducibility:

```python
import json
from datetime import datetime

# Prepare export package
export_data = {
    "symbols": [s.model_dump() for s in engine.symbol_registry.values()],
    "context": context.model_dump(),
    "exported_at": datetime.now().isoformat()
}

# Save to file
with open("bindlang_export.json", "w") as f:
    json.dump(export_data, f, indent=2)

# Load and restore
with open("bindlang_export.json") as f:
    data = json.load(f)

from bindlang import LatentSymbol, Context, BindingEngine

engine = BindingEngine()

# Restore symbols
for symbol_data in data["symbols"]:
    symbol = LatentSymbol.model_validate(symbol_data)
    engine.register(symbol)

# Restore context
context = Context.model_validate(data["context"])

# Bind
activated = engine.bind_all_registered(context)
```

---

## JSONL Format (Line-Delimited)

For large datasets or streaming:

```python
import json

# Write symbols as JSONL (one per line)
with open("symbols.jsonl", "w") as f:
    for symbol in engine.symbol_registry.values():
        f.write(symbol.model_dump_json() + "\n")

# Read JSONL back
from bindlang import LatentSymbol

symbols = []
with open("symbols.jsonl") as f:
    for line in f:
        symbol = LatentSymbol.model_validate_json(line.strip())
        symbols.append(symbol)
```

---

## Audit Trail Storage

### Real-time Streaming

Stream audit data during binding using sinks:

```python
from bindlang import BindingEngine
from bindlang.core.sinks import JSONLFileSink, JSONFileSink

# Stream to JSONL file
sink = JSONLFileSink("audit.jsonl", buffer_size=10)
with BindingEngine(audit_sink=sink) as engine:
    # ... register and bind symbols ...
    pass  # Auto-flushes and closes

# Stream to JSON array
sink = JSONFileSink("audit.json")
with BindingEngine(audit_sink=sink) as engine:
    # ... register and bind symbols ...
    pass
```

See [examples/custom_sinks/](../../examples/custom_sinks/) for custom storage backends (SQLite, in-memory, multiplex).

### Post-hoc Export

Export audit trail after binding from memory:

```python
# Export full audit trail
engine.export.trail("audit.json")
engine.export.trail("audit.jsonl", fmt="jsonl")

# Export only failures
count = engine.export.failures("failures.json")
print(f"Exported {count} failures")
```

---

## Next Steps

- [BindingEngine](engine.md) - Export audit trail
- [Debugging](debugging.md) - Analyze exported data
- [Models](models.md) - Understand data structure
