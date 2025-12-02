"""
Symbol templates for validation and reusability.

Enforces payload structure, validates types, and provides JSON schemas.
"""

from __future__ import annotations

import re
from typing import Dict, List, Set, Optional, Any
from pydantic import BaseModel, Field, model_validator

from .models import GateCondition, LatentSymbol


class SymbolTemplate(BaseModel):
    """Template for validating and creating symbols with consistent structure."""

    symbol_type_pattern: str = Field(
        ...,
        description="Pattern for symbol types (must contain '*' wildcard)"
    )
    required_payload_fields: Set[str] = Field(
        default_factory=set,
        description="Fields required in symbol payload"
    )
    optional_payload_fields: Set[str] = Field(
        default_factory=set,
        description="Fields optionally present in symbol payload"
    )
    gate_requirements: Dict[str, Any] = Field(
        default_factory=dict,
        description="Requirements for gate conditions"
    )
    default_gate: Optional[GateCondition] = Field(
        default=None,
        description="Default gate condition if none provided"
    )

    @model_validator(mode="after")
    def validate_template(self) -> 'SymbolTemplate':
        """Validate template has non-empty pattern with '*' wildcard."""
        if not self.symbol_type_pattern:
            raise ValueError("symbol_type_pattern is required")
        if "*" not in self.symbol_type_pattern:
            raise ValueError("symbol_type_pattern must contain '*' wildcard")
        return self

    def matches_symbol_type(self, symbol_type: str) -> bool:
        """Check if symbol type matches template pattern."""
        # Convert pattern to regex: "CHARSTATE:*" -> "^CHARSTATE:.*$"
        pattern = self.symbol_type_pattern.replace("*", ".*")
        return bool(re.match(f"^{pattern}$", symbol_type))

    def create(
        self,
        id: str,
        symbol_type: str,
        payload: Dict[str, Any],
        gate: Optional[GateCondition] = None,
        metadata: Optional[Dict[str, Any]] = None,
        depends_on: Optional[List[str]] = None
    ) -> LatentSymbol:
        """Create validated LatentSymbol from template."""
        # Validate symbol type matches pattern
        if not self.matches_symbol_type(symbol_type):
            raise ValueError(
                f"Symbol type '{symbol_type}' doesn't match template pattern "
                f"'{self.symbol_type_pattern}'"
            )

        # Validate required payload fields
        missing_fields = self.required_payload_fields - set(payload.keys())
        if missing_fields:
            raise ValueError(
                f"Missing required payload fields: {', '.join(sorted(missing_fields))}"
            )

        # Use provided gate or default gate
        final_gate = gate or self.default_gate
        if final_gate is None:
            raise ValueError(
                "No gate condition provided and no default gate in template"
            )

        # Custom validation hook (override in subclasses)
        self.validate_payload(payload)

        return LatentSymbol(
            id=id,
            symbol_type=symbol_type,
            gate=final_gate,
            payload=payload,
            metadata=metadata or {},
            depends_on=depends_on or []
        )

    def validate_payload(self, payload: Dict[str, Any]) -> None:
        """Override for custom payload validation (called after required field check)."""
        pass

    def to_json_schema(self) -> Dict[str, Any]:
        """Generate JSON schema for LLM integration."""
        return {
            "symbol_type_pattern": self.symbol_type_pattern,
            "required_payload_fields": sorted(self.required_payload_fields),
            "optional_payload_fields": sorted(self.optional_payload_fields),
            "gate_requirements": self.gate_requirements
        }
