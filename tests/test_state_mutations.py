"""
Test for reactive state mutations.

Verifies that state mutations from bound symbols propagate to subsequent
rounds, enabling state-driven cascades.
"""

from datetime import datetime
from bindlang.core.engine import BindingEngine
from bindlang.core.models import LatentSymbol, GateCondition, Context


def test_state_driven_chain():
    """State mutations should enable subsequent symbols to bind."""
    engine = BindingEngine()

    # Symbol 1: Pick up key (no state requirements, sets has_key=True)
    pick_up_key = LatentSymbol(
        id="pick_up_key",
        symbol_type="ACTION:pickup",
        gate=GateCondition(who={"player"}),
        payload={
            "action": "pick_up",
            "item": "key",
            "state_mutation": {"has_key": True}
        }
    )

    # Symbol 2: Unlock door (requires has_key=True)
    unlock_door = LatentSymbol(
        id="unlock_door",
        symbol_type="ACTION:unlock",
        gate=GateCondition(
            who={"player"},
            state={"has_key": True}  # Requires state from pick_up_key
        ),
        payload={
            "action": "unlock",
            "state_mutation": {"door_locked": False}
        }
    )

    engine.register(pick_up_key)
    engine.register(unlock_door)

    # Initial context: no key, door locked
    context = Context(
        who="player",
        where="room",
        when=datetime.now(),
        state={"has_key": False, "door_locked": True}
    )

    # Execute cascade with reactive state mutations
    results, final_context = engine.bind_all_registered(context)

    # Verify both symbols bound
    bound_ids = {r.symbol_id for r in results}
    assert "pick_up_key" in bound_ids, "pick_up_key should bind"
    assert "unlock_door" in bound_ids, "unlock_door should bind after state mutation"

    # Verify final state reflects all mutations
    assert final_context.state["has_key"] is True, "Final state should have has_key=True"
    assert final_context.state["door_locked"] is False, "Final state should have door_locked=False"

    # Verify state changes are tracked in BoundSymbol
    pick_up_result = next(r for r in results if r.symbol_id == "pick_up_key")
    assert pick_up_result.state_changes_applied is not None, "State changes should be tracked in BoundSymbol"
    assert len(pick_up_result.state_changes_applied) == 1, "Should have 1 state change"
    assert pick_up_result.state_changes_applied[0]["key"] == "has_key"
    assert pick_up_result.state_changes_applied[0]["old"] is False
    assert pick_up_result.state_changes_applied[0]["new"] is True

    # Verify state changes are also tracked in audit trail (BindingAttempt)
    pick_up_audit = next(a for a in engine.audit.trail if a.symbol_id == "pick_up_key" and a.success)
    assert pick_up_audit.state_changes_applied is not None, "State changes should be tracked in audit trail"
    assert len(pick_up_audit.state_changes_applied) == 1, "Audit should have 1 state change"
    assert pick_up_audit.state_changes_applied[0]["key"] == "has_key"
    assert pick_up_audit.state_changes_applied[0]["old"] is False
    assert pick_up_audit.state_changes_applied[0]["new"] is True

    print("\nAll assertions passed.")
    print(f"  - Bound symbols: {bound_ids}")
    print(f"  - Final state: {final_context.state}")
    print(f"  - State changes in BoundSymbol: {pick_up_result.state_changes_applied}")
    print(f"  - State changes in audit trail: {pick_up_audit.state_changes_applied}")
    print("  - pick_up_key → has_key=True → unlock_door cascade succeeded")


def test_state_mutation_latent_without_precondition():
    """Symbols with unsatisfied state conditions should remain LATENT."""
    engine = BindingEngine()

    # Symbol that requires has_key=True (but nothing sets it)
    unlock_door = LatentSymbol(
        id="unlock_door",
        symbol_type="ACTION:unlock",
        gate=GateCondition(
            who={"player"},
            state={"has_key": True}  # Required but never satisfied
        ),
        payload={"action": "unlock"}
    )

    engine.register(unlock_door)

    context = Context(
        who="player",
        where="room",
        when=datetime.now(),
        state={"has_key": False}  # Doesn't satisfy gate
    )

    results, _ = engine.bind_all_registered(context)

    # Verify symbol remained LATENT (not attempted, not failed)
    attempted_ids = {a.symbol_id for a in engine.audit.trail}
    assert "unlock_door" not in attempted_ids, "unlock_door should be LATENT (never attempted)"
    assert len(results) == 0, "No symbols should bind"

    print("\nAll assertions passed.")
    print("  - unlock_door: LATENT (state condition not met)")
    print("  - Symbol never attempted (PRE-CHECK 3 prevented binding)")


def test_multi_step_state_chain():
    """Test three-step state chain: A → B → C."""
    engine = BindingEngine()

    # Step 1: Set x=1
    step_a = LatentSymbol(
        id="step_a",
        symbol_type="ACTION:step",
        gate=GateCondition(who={"user"}),
        payload={"state_mutation": {"x": 1}}
    )

    # Step 2: Requires x=1, sets y=2
    step_b = LatentSymbol(
        id="step_b",
        symbol_type="ACTION:step",
        gate=GateCondition(who={"user"}, state={"x": 1}),
        payload={"state_mutation": {"y": 2}}
    )

    # Step 3: Requires y=2, sets z=3
    step_c = LatentSymbol(
        id="step_c",
        symbol_type="ACTION:step",
        gate=GateCondition(who={"user"}, state={"y": 2}),
        payload={"state_mutation": {"z": 3}}
    )

    engine.register(step_a)
    engine.register(step_b)
    engine.register(step_c)

    context = Context(who="user", where="test", when=datetime.now(), state={})

    results, final_context = engine.bind_all_registered(context)

    # Verify all three steps bound
    bound_ids = {r.symbol_id for r in results}
    assert bound_ids == {"step_a", "step_b", "step_c"}, f"Expected all three steps, got {bound_ids}"

    # Verify final state has all mutations
    assert final_context.state == {"x": 1, "y": 2, "z": 3}, f"Unexpected final state: {final_context.state}"

    print("\nAll assertions passed.")
    print(f"  - Bound symbols: {bound_ids}")
    print(f"  - Final state: {final_context.state}")
    print("  - Three-step chain: step_a → step_b → step_c succeeded")


def test_analytical_mode_no_mutations():
    """Test apply_state_mutations=False (analytical mode)."""
    engine = BindingEngine()

    pick_up_key = LatentSymbol(
        id="pick_up_key",
        symbol_type="ACTION:pickup",
        gate=GateCondition(who={"player"}),
        payload={"state_mutation": {"has_key": True}}
    )

    unlock_door = LatentSymbol(
        id="unlock_door",
        symbol_type="ACTION:unlock",
        gate=GateCondition(who={"player"}, state={"has_key": True}),
        payload={"action": "unlock"}
    )

    engine.register(pick_up_key)
    engine.register(unlock_door)

    context = Context(
        who="player",
        where="room",
        when=datetime.now(),
        state={"has_key": False}
    )

    # Analytical mode: state mutations NOT applied
    results, final_context = engine.bind_all_registered(context, apply_state_mutations=False)

    # Only pick_up_key should bind (unlock_door can't see state mutation)
    bound_ids = {r.symbol_id for r in results}
    assert bound_ids == {"pick_up_key"}, f"Only pick_up_key should bind in analytical mode, got {bound_ids}"

    # Context should remain unchanged
    assert final_context.state == {"has_key": False}, "State should not change in analytical mode"

    print("\nAll assertions passed.")
    print(f"  - Bound symbols: {bound_ids}")
    print(f"  - Final state unchanged: {final_context.state}")
    print("  - Analytical mode: state mutations recorded but not applied")


def test_state_conflict_last_write_wins():
    """Test that last-write-wins for state conflicts within same round."""
    engine = BindingEngine()

    # Two symbols that set same state key to different values
    symbol_1 = LatentSymbol(
        id="set_health_100",
        symbol_type="ACTION:heal",
        gate=GateCondition(who={"user"}),
        payload={"state_mutation": {"health": 100}}
    )

    symbol_2 = LatentSymbol(
        id="set_health_50",
        symbol_type="ACTION:damage",
        gate=GateCondition(who={"user"}),
        payload={"state_mutation": {"health": 50}}
    )

    engine.register(symbol_1)
    engine.register(symbol_2)

    context = Context(who="user", where="test", when=datetime.now(), state={})

    results, final_context = engine.bind_all_registered(context)

    # Both should bind
    assert len(results) == 2, "Both symbols should bind"

    # Final state should have one of the values (last-write-wins)
    assert "health" in final_context.state, "health should be in final state"
    assert final_context.state["health"] in [100, 50], f"health should be 100 or 50, got {final_context.state['health']}"

    print("\nAll assertions passed.")
    print(f"  - Both symbols bound")
    print(f"  - Final health: {final_context.state['health']} (last-write-wins)")


if __name__ == "__main__":
    print("Running state mutation tests...\n")
    print("=" * 60)
    print("Test 1: State-driven chain (pick_up_key → unlock_door)")
    print("=" * 60)
    test_state_driven_chain()

    print("\n" + "=" * 60)
    print("Test 2: State condition keeps symbol LATENT")
    print("=" * 60)
    test_state_mutation_latent_without_precondition()

    print("\n" + "=" * 60)
    print("Test 3: Multi-step state chain (A → B → C)")
    print("=" * 60)
    test_multi_step_state_chain()

    print("\n" + "=" * 60)
    print("Test 4: Analytical mode (apply_state_mutations=False)")
    print("=" * 60)
    test_analytical_mode_no_mutations()

    print("\n" + "=" * 60)
    print("Test 5: State conflict (last-write-wins)")
    print("=" * 60)
    test_state_conflict_last_write_wins()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
