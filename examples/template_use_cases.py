"""
Template Use Cases - Domain-Specific Examples

This file demonstrates template usage across different domains:
- Narrative domain (character states, plot threads)
- Multi-agent domain (witnesses, votes)
- Workflow domain (approvals, notifications)
"""

from bindlang import BindingEngine, GateCondition
from bindlang.core.templates import SymbolTemplate


# ============================================================================
# NARRATIVE DOMAIN
# ============================================================================

def narrative_templates():
    """Templates for narrative/storytelling applications."""

    # Character state template
    CharacterStateTemplate = SymbolTemplate(
        symbol_type_pattern="CHARSTATE:*",
        required_payload_fields={"character", "emotion", "location"},
        optional_payload_fields={"thinking_about", "trait"},
        default_gate=GateCondition()
    )

    # Plot thread template
    PlotThreadTemplate = SymbolTemplate(
        symbol_type_pattern="PLOT:*",
        required_payload_fields={"thread_id", "status", "characters_involved"},
        optional_payload_fields={"deadline", "stakes"},
        default_gate=GateCondition()
    )

    # Example usage
    engine = BindingEngine()
    engine.templates.register(CharacterStateTemplate)
    engine.templates.register(PlotThreadTemplate)

    # Create character state symbol
    anna_brave = engine.templates.create(
        template_pattern="CHARSTATE:*",
        id="char_anna_brave",
        symbol_type="CHARSTATE:brave",
        payload={
            "character": "Anna",
            "emotion": "brave",
            "location": "beach",
            "thinking_about": "David"
        },
        gate=GateCondition(where={"chapter_5"})
    )

    # Create plot thread symbol
    separation = engine.templates.create(
        template_pattern="PLOT:*",
        id="plot_separation",
        symbol_type="PLOT:conflict",
        payload={
            "thread_id": "separation_arc",
            "status": "active",
            "characters_involved": ["Anna", "David"],
            "stakes": "relationship"
        },
        gate=GateCondition(where={"chapter_3", "chapter_4", "chapter_5"})
    )

    print("Narrative templates registered:")
    print(f"  - {anna_brave.symbol_type}")
    print(f"  - {separation.symbol_type}")


# ============================================================================
# MULTI-AGENT DOMAIN
# ============================================================================

def multi_agent_templates():
    """Templates for multi-agent systems."""

    # Witness template
    WitnessTemplate = SymbolTemplate(
        symbol_type_pattern="WITNESS:*",
        required_payload_fields={"agent_id", "role", "target_id"},
        optional_payload_fields={"confidence", "timestamp"},
        default_gate=GateCondition()
    )

    # Vote template
    VoteTemplate = SymbolTemplate(
        symbol_type_pattern="VOTE:*",
        required_payload_fields={"agent_id", "vote_type", "proposal_id"},
        optional_payload_fields={"reasoning", "weight"},
        default_gate=GateCondition()
    )

    # Example usage
    engine = BindingEngine()
    engine.templates.register(WitnessTemplate)
    engine.templates.register(VoteTemplate)

    # Create witness symbol
    witness_1 = engine.templates.create(
        template_pattern="WITNESS:*",
        id="witness_1",
        symbol_type="WITNESS:attest",
        payload={
            "agent_id": "agent_1",
            "role": "witness",
            "target_id": "data_X",
            "confidence": 0.95
        },
        gate=GateCondition(who={"agent_1"}, state={"target_id": "data_X"})
    )

    # Create vote symbol
    vote_1 = engine.templates.create(
        template_pattern="VOTE:*",
        id="vote_1",
        symbol_type="VOTE:approve",
        payload={
            "agent_id": "agent_1",
            "vote_type": "approve",
            "proposal_id": "prop_42",
            "reasoning": "Meets safety criteria",
            "weight": 1.0
        },
        gate=GateCondition(who={"agent_1"}, state={"proposal_id": "prop_42"})
    )

    print("Multi-agent templates registered:")
    print(f"  - {witness_1.symbol_type}")
    print(f"  - {vote_1.symbol_type}")


# ============================================================================
# WORKFLOW DOMAIN
# ============================================================================

def workflow_templates():
    """Templates for workflow automation."""

    # Approval template
    ApprovalTemplate = SymbolTemplate(
        symbol_type_pattern="APPROVAL:*",
        required_payload_fields={"approver_role", "document_id", "decision"},
        optional_payload_fields={"comments", "conditions"},
        default_gate=GateCondition()
    )

    # Notification template
    NotificationTemplate = SymbolTemplate(
        symbol_type_pattern="NOTIFICATION:*",
        required_payload_fields={"recipient", "message", "priority"},
        optional_payload_fields={"channel", "delay"},
        default_gate=GateCondition()
    )

    # Example usage
    engine = BindingEngine()
    engine.templates.register(ApprovalTemplate)
    engine.templates.register(NotificationTemplate)

    # Create approval symbol
    approval = engine.templates.create(
        template_pattern="APPROVAL:*",
        id="approval_1",
        symbol_type="APPROVAL:manager",
        payload={
            "approver_role": "manager",
            "document_id": "doc_123",
            "decision": "approved",
            "comments": "Looks good"
        },
        gate=GateCondition(
            who={"manager"},
            state={"document_id": "doc_123", "stage": "review"}
        )
    )

    # Create notification symbol
    notification = engine.templates.create(
        template_pattern="NOTIFICATION:*",
        id="notif_1",
        symbol_type="NOTIFICATION:email",
        payload={
            "recipient": "alice@example.com",
            "message": "Your approval is needed",
            "priority": "high",
            "channel": "email"
        },
        gate=GateCondition(
            where={"approval_required"},
            state={"trigger_event": "doc_submitted"}
        )
    )

    print("Workflow templates registered:")
    print(f"  - {approval.symbol_type}")
    print(f"  - {notification.symbol_type}")


# ============================================================================
# RUN ALL EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEMPLATE USE CASES")
    print("=" * 60)
    print()

    print("1. Narrative Domain")
    print("-" * 60)
    narrative_templates()
    print()

    print("2. Multi-Agent Domain")
    print("-" * 60)
    multi_agent_templates()
    print()

    print("3. Workflow Domain")
    print("-" * 60)
    workflow_templates()
    print()

    print("=" * 60)
    print("Done.")
    print("=" * 60)
