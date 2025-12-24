"""
Composition operators for bindlang.

Usage:
    resilient = sym(primary) | sym(fallback)
    sequential = sym(gate) >> sym(action)
    parallel = sym(a) & sym(b) & sym(c)
    result = resilient.try_bind(context, engine)
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Protocol, TYPE_CHECKING, Union, List

if TYPE_CHECKING:
    from .engine import BindingEngine
    from .models import Context

from .models import BoundSymbol, LatentSymbol


class BindingStatus(Enum):
    BOUND = "bound"
    LATENT = "latent"


@dataclass(frozen=True)
class BindingResult:
    status: BindingStatus
    bound: Optional[BoundSymbol] = None
    bound_all: Optional[List[BoundSymbol]] = None
    source: Optional[LatentSymbol] = None

    @classmethod
    def success(cls, bound: BoundSymbol) -> BindingResult:
        return cls(status=BindingStatus.BOUND, bound=bound)

    @classmethod
    def success_all(cls, bound_list: List[BoundSymbol]) -> BindingResult:
        return cls(status=BindingStatus.BOUND, bound=bound_list[-1], bound_all=bound_list)

    @classmethod
    def still_latent(cls, symbol: LatentSymbol) -> BindingResult:
        return cls(status=BindingStatus.LATENT, source=symbol)

    @property
    def is_bound(self) -> bool:
        return self.status == BindingStatus.BOUND


class Bindable(Protocol):
    def try_bind(self, context: "Context", engine: "BindingEngine") -> BindingResult:
        ...


class Sym:
    """Wrapper for LatentSymbol that enables composition operators."""

    def __init__(self, symbol: LatentSymbol):
        self.symbol = symbol

    def try_bind(self, context: "Context", engine: "BindingEngine") -> BindingResult:
        result = engine.bind(self.symbol, context)
        if result is not None:
            return BindingResult.success(result)
        return BindingResult.still_latent(self.symbol)

    def __or__(self, other: Bindable) -> "Alternative":
        return Alternative(self, other)

    def __rshift__(self, other: Bindable) -> "Sequential":
        return Sequential(self, other)

    def __and__(self, other: Bindable) -> "Parallel":
        return Parallel([self, other])

    def __repr__(self) -> str:
        return f"Sym({self.symbol.id})"


class Alternative:
    """Try left, if latent try right."""

    def __init__(self, left: Bindable, right: Bindable):
        self.left = left
        self.right = right

    def try_bind(self, context: "Context", engine: "BindingEngine") -> BindingResult:
        result = self.left.try_bind(context, engine)
        if result.is_bound:
            return result
        return self.right.try_bind(context, engine)

    def __or__(self, other: Bindable) -> "Alternative":
        return Alternative(self, other)

    def __rshift__(self, other: Bindable) -> "Sequential":
        return Sequential(self, other)

    def __and__(self, other: Bindable) -> "Parallel":
        return Parallel([self, other])

    def __repr__(self) -> str:
        return f"({self.left} | {self.right})"


class Sequential:
    """Left must bind before right is attempted."""

    def __init__(self, left: Bindable, right: Bindable):
        self.left = left
        self.right = right

    def try_bind(self, context: "Context", engine: "BindingEngine") -> BindingResult:
        left_result = self.left.try_bind(context, engine)
        if not left_result.is_bound:
            return left_result
        return self.right.try_bind(context, engine)

    def __or__(self, other: Bindable) -> "Alternative":
        return Alternative(self, other)

    def __rshift__(self, other: Bindable) -> "Sequential":
        return Sequential(self, other)

    def __and__(self, other: Bindable) -> "Parallel":
        return Parallel([self, other])

    def __repr__(self) -> str:
        return f"({self.left} >> {self.right})"


class Parallel:
    """All must bind for success."""

    def __init__(self, items: List[Bindable]):
        self.items = items

    def try_bind(self, context: "Context", engine: "BindingEngine") -> BindingResult:
        results = [item.try_bind(context, engine) for item in self.items]
        if all(r.is_bound for r in results):
            bound_list = [r.bound for r in results if r.bound]
            return BindingResult.success_all(bound_list)
        # Return first latent
        for r in results:
            if not r.is_bound:
                return r
        return results[0]

    def __or__(self, other: Bindable) -> "Alternative":
        return Alternative(self, other)

    def __rshift__(self, other: Bindable) -> "Sequential":
        return Sequential(self, other)

    def __and__(self, other: Bindable) -> "Parallel":
        return Parallel(self.items + [other])

    def __repr__(self) -> str:
        return f"({' & '.join(str(i) for i in self.items)})"


def sym(symbol: LatentSymbol) -> Sym:
    return Sym(symbol)
