"""
Template management for BindingEngine.

Handles symbol template registration and creation from templates.
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING

from .models import LatentSymbol, GateCondition
from .templates import SymbolTemplate

if TYPE_CHECKING:
    from .engine import BindingEngine


class TemplateManager:
    """Manages symbol templates and creation from templates."""

    def __init__(self, engine: 'BindingEngine'):
        self.engine = engine
        self.registry: Dict[str, SymbolTemplate] = {}

    def register(self, template: SymbolTemplate) -> None:
        """Register a symbol template."""
        self.registry[template.symbol_type_pattern] = template

    def find_by_symbol_type(self, symbol_type: str) -> Optional[SymbolTemplate]:
        """Find template that matches the given symbol_type using pattern matching."""
        for template in self.registry.values():
            if template.matches_symbol_type(symbol_type):
                return template
        return None

    def create(
        self,
        template_pattern: str,
        id: str,
        symbol_type: str,
        payload: Dict[str, Any],
        gate: Optional[GateCondition] = None,
        metadata: Optional[Dict[str, Any]] = None,
        depends_on: Optional[List[str]] = None,
        auto_register: bool = True
    ) -> LatentSymbol:
        """Create symbol from registered template (optionally auto-register).

        First tries exact pattern match, then falls back to pattern matching
        against symbol_type if no exact match is found.
        """
        # Try exact pattern match first
        template = self.registry.get(template_pattern)

        # Fall back to pattern matching if no exact match
        if not template:
            template = self.find_by_symbol_type(symbol_type)

        if not template:
            raise ValueError(
                f"Template not found for pattern '{template_pattern}' or symbol_type '{symbol_type}'. "
                f"Available templates: {list(self.registry.keys())}"
            )

        symbol = template.create(
            id=id,
            symbol_type=symbol_type,
            payload=payload,
            gate=gate,
            metadata=metadata,
            depends_on=depends_on
        )

        if auto_register:
            self.engine.register(symbol)

        return symbol
