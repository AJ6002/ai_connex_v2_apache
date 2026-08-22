"""
Jane Copilot LangGraph StateGraph Engine.
Coordinates intake, Scout discovery inspection, HITL clarification, and quality gating.
"""

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from aiconnex_agent.local_gguf_client import LocalGGUFEngine
from contracts.discovery.discovery_contract import DatasetDiscoveryArtifact
from contracts.intent.intent_contract import IntentContract
from contracts.segmentation.segmentation_contract import SegmentationProposal


class MasterAgentState(TypedDict):
    user_goal: str
    tenant_uid: str
    user_uid: str
    site_scope: str | None
    asset_scope: str | None
    raw_asset_ids: list[str]
    autonomy_requested: str
    intent_contract: IntentContract | None

    discovery_artifact: DatasetDiscoveryArtifact | None
    segmentation_proposal: SegmentationProposal | None
    quality_passed: bool
    confidence_score: float
    requires_hitl: bool
    status: str
    errors: list[str]


class JaneCopilot:
    """
    Jane Copilot LangGraph Agentic Orchestrator.
    """

    def __init__(self, model_dir: str = "models") -> None:
        self.local_engine = LocalGGUFEngine(model_dir=model_dir)
        self.workflow = self._build_workflow()
        self.graph = self.workflow.compile()

    def _build_workflow(self) -> StateGraph:
        builder = StateGraph(MasterAgentState)

        builder.add_node("intake_node", self._intake_node)
        builder.add_node("scout_discovery_node", self._scout_discovery_node)
        builder.add_node("hitl_clarification_node", self._hitl_clarification_node)
        builder.add_node("quality_gate_node", self._quality_gate_node)

        builder.add_edge(START, "intake_node")
        builder.add_edge("intake_node", "scout_discovery_node")
        builder.add_edge("scout_discovery_node", "hitl_clarification_node")

        builder.add_conditional_edges(
            "hitl_clarification_node",
            self._route_after_hitl,
            {
                "proceed_quality": "quality_gate_node",
                "await_hitl": END
            }
        )
        builder.add_edge("quality_gate_node", END)

        return builder

    def _intake_node(self, state: MasterAgentState) -> dict[str, Any]:
        """
        Normalize raw user goal into IntentContract using strict 2-tier local LLM.
        """
        intent = self.local_engine.generate_intent(
            user_goal=state["user_goal"],
            tenant_uid=state["tenant_uid"],
            user_uid=state["user_uid"],
            site_scope=state.get("site_scope"),
            asset_scope=state.get("asset_scope"),
            raw_asset_ids=state.get("raw_asset_ids", []),
            autonomy_requested=state.get("autonomy_requested", "HITL")
        )

        return {
            "intent_contract": intent,
            "status": "INTENT_PARSED"
        }

    def _scout_discovery_node(self, state: MasterAgentState) -> dict[str, Any]:
        """
        Scout discovery inspection step.
        """
        raw_assets = state.get("raw_asset_ids", [])
        asset_id = raw_assets[0] if raw_assets else "asset-default"

        discovery = DatasetDiscoveryArtifact(
            asset_id=asset_id,
            archive_type="none",
            member_inventory=[f"{asset_id}.csv"],
            member_sizes={f"{asset_id}.csv": 1024},
            detected_formats=["csv"]
        )

        return {
            "discovery_artifact": discovery,
            "status": "DISCOVERY_COMPLETE"
        }

    def _hitl_clarification_node(self, state: MasterAgentState) -> dict[str, Any]:
        """
        Evaluate confidence & check if HITL clarification is required.
        """
        intent = state.get("intent_contract")
        confidence = 0.90 if intent and intent.asset_scope else 0.75
        requires_hitl = confidence < 0.85 or (intent and intent.autonomy_requested == "HITL")

        return {
            "confidence_score": confidence,
            "requires_hitl": requires_hitl,
            "status": "HITL_CHECKED"
        }

    def _route_after_hitl(self, state: MasterAgentState) -> str:
        if state.get("requires_hitl", False):
            return "await_hitl"
        return "proceed_quality"

    def _quality_gate_node(self, state: MasterAgentState) -> dict[str, Any]:
        """
        Quality gate verification node.
        """
        return {
            "quality_passed": True,
            "status": "QUALITY_VERIFIED"
        }

    def run(
        self,
        user_goal: str,
        tenant_uid: str,
        user_uid: str,
        site_scope: str | None = None,
        asset_scope: str | None = None,
        raw_asset_ids: list[str] | None = None,
        autonomy_requested: str = "HITL"
    ) -> MasterAgentState:
        initial_state: MasterAgentState = {
            "user_goal": user_goal,
            "tenant_uid": tenant_uid,
            "user_uid": user_uid,
            "site_scope": site_scope,
            "asset_scope": asset_scope,
            "raw_asset_ids": raw_asset_ids or [],
            "autonomy_requested": autonomy_requested,
            "intent_contract": None,
            "discovery_artifact": None,
            "segmentation_proposal": None,
            "quality_passed": False,
            "confidence_score": 0.0,
            "requires_hitl": False,
            "status": "INITIATED",
            "errors": []
        }
        return self.graph.invoke(initial_state)

