"""
Test for temporal pre-check.

Verifies that symbols with future temporal conditions remain LATENT
instead of being attempted and marked as FAILED.
"""

from datetime import datetime
from bindlang.core.engine import BindingEngine
from bindlang.core.models import LatentSymbol, GateCondition, Context


def test_future_temporal_remains_latent():
    """Symbols with future temporal gates should remain LATENT."""
    engine = BindingEngine()

    # Symbol with future temporal condition
    future_symbol = LatentSymbol(
        id="scheduled_2099",
        symbol_type="EVENT:scheduled",
        gate=GateCondition(when="after:2099-01-01T00:00:00"),
        payload={"event": "future_maintenance"}
    )

    # Symbol with past temporal condition (should activate)
    past_symbol = LatentSymbol(
        id="scheduled_2020",
        symbol_type="EVENT:scheduled",
        gate=GateCondition(when="after:2020-01-01T00:00:00"),
        payload={"event": "past_event"}
    )

    engine.register(future_symbol)
    engine.register(past_symbol)

    # Context in present time
    context = Context(
        who="system",
        where="scheduler",
        when=datetime(2024, 11, 16),
        state={}
    )

    results, _ = engine.bind_all_registered(context)

    # Verify states
    attempted_ids = {a.symbol_id for a in engine.audit.trail}
    bound_ids = {r.symbol_id for r in results}
    all_ids = {"scheduled_2099", "scheduled_2020"}
    latent_ids = all_ids - attempted_ids

    print(f"\nResults:")
    print(f"  Bound: {bound_ids}")
    print(f"  Attempted: {attempted_ids}")
    print(f"  Latent (not attempted): {latent_ids}")

    # Verify expected behavior
    assert "scheduled_2020" in bound_ids, "Past temporal should bind"
    assert "scheduled_2099" not in attempted_ids, "Future temporal should be LATENT (never attempted)"
    assert latent_ids == {"scheduled_2099"}, f"Expected scheduled_2099 to be latent, got {latent_ids}"

    print("\nAll assertions passed.")
    print("  - scheduled_2020: BOUND (past temporal condition)")
    print("  - scheduled_2099: LATENT (future temporal condition - not attempted)")


if __name__ == "__main__":
    test_future_temporal_remains_latent()
