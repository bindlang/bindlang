# Templates

[Back to Reference](index.md)

Reusable blueprints for creating symbols with validation.

---

## Basic Template

```python
from bindlang.core.templates import SymbolTemplate
from bindlang import GateCondition

template = SymbolTemplate(
    symbol_type_pattern="CHARSTATE:*",
    required_payload_fields={"character", "emotion", "location"},
    optional_payload_fields={"thinking_about"},
    default_gate=GateCondition()  # Optional default
)

# Create symbol from template
anna = template.create(
    id="anna_brave",
    symbol_type="CHARSTATE:brave",
    payload={"character": "Anna", "emotion": "brave", "location": "beach"},
    gate=GateCondition(where={"chapter_5"})
)
```

**Visual reference:** [Template System diagram](../diagrams/template-system.md#symboltemplate-architecture) shows the template architecture, engine integration, and validation flow.

---

## SymbolTemplate

### Constructor

```python
from bindlang.core.templates import SymbolTemplate

template = SymbolTemplate(
    symbol_type_pattern: str,
    required_payload_fields: Set[str] = set(),
    optional_payload_fields: Set[str] = set(),
    gate_requirements: Dict[str, Any] = {},
    default_gate: Optional[GateCondition] = None
)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol_type_pattern` | `str` | Yes | Pattern with `*` wildcard (e.g., `"VOTE:*"`) |
| `required_payload_fields` | `Set[str]` | No | Fields that must be in payload |
| `optional_payload_fields` | `Set[str]` | No | Fields that may be in payload |
| `gate_requirements` | `Dict[str, Any]` | No | Gate requirements (future use) |
| `default_gate` | `Optional[GateCondition]` | No | Default gate if none provided |

---

## Methods

### create()

Create a LatentSymbol from template with validation.

```python
def create(
    id: str,
    symbol_type: str,
    payload: Dict[str, Any],
    gate: Optional[GateCondition] = None,
    metadata: Optional[Dict[str, Any]] = None,
    depends_on: Optional[List[str]] = None
) -> LatentSymbol
```

**Validation:**
1. Checks symbol_type matches pattern
2. Checks required fields present in payload
3. Calls custom `validate_payload()` hook
4. Creates LatentSymbol

**Example:**
```python
symbol = template.create(
    id="anna_brave",
    symbol_type="CHARSTATE:brave",
    payload={"character": "Anna", "emotion": "brave", "location": "beach"},
    gate=GateCondition(where={"chapter_5"})
)
```

**Raises:** `ValueError` if validation fails

---

### matches_symbol_type()

Check if a symbol type matches template pattern.

```python
def matches_symbol_type(symbol_type: str) -> bool
```

**Example:**
```python
template = SymbolTemplate(symbol_type_pattern="CHARSTATE:*")
template.matches_symbol_type("CHARSTATE:brave")  # True
template.matches_symbol_type("VOTE:promote")     # False
```

---

### to_json_schema()

Generate JSON schema for template.

```python
def to_json_schema() -> Dict[str, Any]
```

**Example:**
```python
schema = template.to_json_schema()
print(schema)
# Output:
# {
#     'symbol_type_pattern': 'CHARSTATE:*',
#     'required_payload_fields': ['character', 'emotion', 'location'],
#     'optional_payload_fields': ['thinking_about'],
#     'gate_requirements': {}
# }
```

**Use case:** LLM integration - provide schema to LLM for symbol generation

---

## Custom Validation

Override `validate_payload()` for domain-specific constraints.

```python
from bindlang.core.templates import SymbolTemplate

class CharacterStateTemplate(SymbolTemplate):
    def validate_payload(self, payload):
        valid_emotions = {"brave", "scared", "happy", "sad", "angry", "confused"}
        emotion = payload.get("emotion")

        if emotion not in valid_emotions:
            raise ValueError(
                f"Invalid emotion: '{emotion}'. "
                f"Must be one of: {', '.join(sorted(valid_emotions))}"
            )

# Use custom template
template = CharacterStateTemplate(
    symbol_type_pattern="CHARSTATE:*",
    required_payload_fields={"character", "emotion", "location"}
)

# Valid
anna = template.create(
    id="anna_brave",
    symbol_type="CHARSTATE:brave",
    payload={"character": "Anna", "emotion": "brave", "location": "beach"}
)

# Invalid - raises ValueError
try:
    bad = template.create(
        id="anna_bad",
        symbol_type="CHARSTATE:unknown",
        payload={"character": "Anna", "emotion": "curious", "location": "beach"}
    )
except ValueError as e:
    print(e)  # Invalid emotion: 'curious'. Must be one of: angry, brave, ...
```

---

## Using with BindingEngine

Register templates and create symbols via template manager:

```python
from bindlang import BindingEngine, GateCondition
from bindlang.core.templates import SymbolTemplate

engine = BindingEngine()

# Register template via template manager
template = SymbolTemplate(
    symbol_type_pattern="WITNESS:*",
    required_payload_fields={"agent_id", "role", "target_id"}
)
engine.templates.register(template)

# Create symbol from template via template manager
symbol = engine.templates.create(
    template_pattern="WITNESS:*",
    id="witness_1",
    symbol_type="WITNESS:attest",
    payload={"agent_id": "agent_1", "role": "witness", "target_id": "data_X"},
    gate=GateCondition(who={"agent_1"})
)

# Symbol is automatically registered (auto_register=True by default)
```

---

## Next Steps

- [BindingEngine](engine.md) - Use templates with engine
- [Common Patterns](patterns.md) - See templates in action
- [Models](models.md) - Understand LatentSymbol structure
