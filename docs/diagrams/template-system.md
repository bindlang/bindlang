# Template System - Reusable Contracts

## SymbolTemplate Architecture

```mermaid
graph TB
    subgraph "SymbolTemplate - Base Class"
        BaseT[SymbolTemplate<br/>━━━━━━━━━<br/>symbol_type_pattern: str<br/>required_payload_fields: Set<br/>optional_payload_fields: Set<br/>gate_requirements: Dict<br/>default_gate: GateCondition]

        Methods[Methods<br/>━━━━━━━━━<br/>create<br/>validate_payload<br/>to_json_schema]

        BaseT --> Methods
    end

    subgraph "Concrete Templates"
        CharT[CharacterStateTemplate<br/>CHARSTATE:*<br/>required: character, emotion, location<br/>validates: emotion in valid list]

        VoteT[VoteTemplate<br/>VOTE:*<br/>required: agent_id, target_id, vote_value<br/>validates: weight 0.0-2.0]

        ApprovalT[ApprovalTemplate<br/>APPROVAL:*<br/>required: approver, document_id, status<br/>validates: status enum]

        CharT -.extends.-> BaseT
        VoteT -.extends.-> BaseT
        ApprovalT -.extends.-> BaseT
    end

    subgraph "Engine Integration"
        Engine2[BindingEngine]
        TManager[engine.templates<br/>TemplateManager]
        TRegistry[registry<br/>Dict: pattern → Template]

        CreateMethod[templates.create<br/>Validates + Creates]

        Engine2 --> TManager
        TManager --> TRegistry
        TManager --> CreateMethod

        CreateMethod -.uses.-> BaseT
    end

    style BaseT fill:#E1BEE7,color:#000
    style CharT fill:#CE93D8,color:#000
    style VoteT fill:#BA68C8,color:#000
    style ApprovalT fill:#AB47BC,color:#000
```

## Template Lifecycle

**1. Define Template**
```python
from bindlang.core.templates import SymbolTemplate
from bindlang import GateCondition

vote_template = SymbolTemplate(
    symbol_type_pattern="VOTE:*",
    required_payload_fields={"agent_id", "target_id", "vote_value"},
    optional_payload_fields={"weight", "timestamp"},
    default_gate=GateCondition(who={"voter"})
)
```

**2. Register Template**
```python
from bindlang import BindingEngine

engine = BindingEngine()
engine.templates.register(vote_template)
```

**3. Create Symbols from Template**
```python
# Template validates payload automatically
vote = engine.templates.create(
    template_pattern="VOTE:*",
    id="vote_promote_bob",
    symbol_type="VOTE:promote",
    payload={"agent_id": "alice", "target_id": "bob", "vote_value": 1.0},
    gate=GateCondition(who={"admin"})  # Override default
)
```

**4. Validation Enforcement**
```python
# Raises ValueError: missing required field 'target_id'
vote = engine.templates.create(
    template_pattern="VOTE:*",
    id="vote_invalid",
    symbol_type="VOTE:promote",
    payload={"agent_id": "alice", "vote_value": 1.0}
)
```

## JSON Schema Generation

Templates can generate JSON schemas for LLM integration:

```python
template = VoteTemplate()
schema = template.to_json_schema()

# Returns:
{
    "type": "object",
    "properties": {
        "agent_id": {"type": "string"},
        "target_id": {"type": "string"},
        "vote_value": {"type": "number"},
        "weight": {"type": "number"},  # optional
        "timestamp": {"type": "string"}  # optional
    },
    "required": ["agent_id", "target_id", "vote_value"]
}
```

## See Also

- [Core Architecture](core-architecture.md)
- [Templates Reference](../reference/templates.md)
- [Pattern Library](../reference/patterns.md)
