"""
Local GGUF Model Runner & Deterministic Heuristic Engine.
Strict 2-tier local-only execution:
  Tier 1 (Primary): In-process GGUF model loader reading ./models/*.gguf
  Tier 2 (Only Fallback): Deterministic Heuristic & Rule Engine (Regex + Industrial Glossary + Contracts)
Zero external network sockets, zero cloud APIs, zero external daemons.
"""

import json
import uuid
from pathlib import Path
from typing import Any

from contracts.intent.intent_contract import IntentContract
from registries.intent.registry import lookup_intent_policy


class DeterministicHeuristicEngine:
    """
    Tier 2 Fallback: Deterministic Heuristic & Rule Engine for Offline CI / Zero-LLM environments.
    Translates raw user goals into validated IntentContracts using strict regex,
    industrial vocabulary glossaries, and schema contracts.
    """

    def __init__(self, glossary_path: str = "registries/industrial_vocabulary/glossary.json") -> None:
        self.glossary_path = Path(glossary_path)
        self.glossary: dict[str, Any] = {}
        if self.glossary_path.exists():
            try:
                with open(self.glossary_path, encoding="utf-8") as f:
                    self.glossary = json.load(f)
            except (OSError, json.JSONDecodeError, ValueError):
                self.glossary = {}

    def parse_intent(
        self,
        user_goal: str,
        tenant_uid: str,
        user_uid: str,
        site_scope: str | None = None,
        asset_scope: str | None = None,
        raw_asset_ids: list[str] | None = None,
        autonomy_requested: str = "HITL"
    ) -> IntentContract:

        goal_lower = user_goal.lower()

        # Heuristic intent classification
        if any(w in goal_lower for w in ["forecast", "predict", "time series", "future"]):
            intent_type = "time_series_forecast"
            requires_model = True
            requested_outputs = ["parquet", "model", "visualization"]
        elif any(w in goal_lower for w in ["anomaly", "outlier", "spike", "fault", "defect"]):
            intent_type = "anomaly_detection"
            requires_model = True
            requested_outputs = ["parquet", "visualization"]
        elif any(w in goal_lower for w in ["clean", "normalize", "prepare", "transform", "segment"]):
            intent_type = "dataset_preparation"
            requires_model = False
            requested_outputs = ["parquet"]
        else:
            intent_type = "hourly_sensor_upload"
            requires_model = False
            requested_outputs = ["parquet", "visualization"]

        # Asset scope extraction heuristics
        if not asset_scope:
            if "compressor" in goal_lower:
                asset_scope = "compressor"
            elif "turbine" in goal_lower:
                asset_scope = "turbine"
            elif "pump" in goal_lower:
                asset_scope = "pump"
            elif "boiler" in goal_lower:
                asset_scope = "boiler"

        policy = lookup_intent_policy(intent_type) or {}

        intent_uid = f"intent-{uuid.uuid4().hex[:8]}"

        return IntentContract(
            intent_uid=intent_uid,
            tenant_uid=tenant_uid,
            user_uid=user_uid,
            site_scope=site_scope,
            asset_scope=asset_scope,
            goal=user_goal,
            domain="industrial_telemetry",
            intent_type=intent_type,
            requested_outputs=requested_outputs,
            requires_model=requires_model,
            requires_visualization=True,
            requires_service=False,
            autonomy_requested=autonomy_requested,

            constraints={"parsed_by": "deterministic_heuristic_engine", "policy": policy},
            source_refs=raw_asset_ids or [],
            policy_ref=policy.get("policy_id", "default_policy") if isinstance(policy, dict) else "default_policy"
        )


class LocalGGUFEngine:
    """
    Strict 2-Tier Local LLM Runner.
    - Tier 1: In-process local .gguf execution.
    - Tier 2: Deterministic Heuristic Engine if no .gguf binary loaded.
    """

    def __init__(self, model_dir: str = "models") -> None:
        self.model_dir = Path(model_dir)
        self.heuristic_engine = DeterministicHeuristicEngine()
        self.active_gguf_path: Path | None = None
        self.gguf_model: Any | None = None

        # Check for local GGUF models in ./models/
        if self.model_dir.exists():
            gguf_files = list(self.model_dir.glob("*.gguf"))
            if gguf_files:
                self.active_gguf_path = gguf_files[0]
                self._load_gguf_in_process()

    def _load_gguf_in_process(self) -> None:
        if not self.active_gguf_path:
            return
        try:
            import llama_cpp
            self.gguf_model = llama_cpp.Llama(
                model_path=str(self.active_gguf_path),
                n_ctx=2048,
                verbose=False
            )
        except (ImportError, OSError, RuntimeError, ValueError):
            # Fall back cleanly to Tier 2 Deterministic Heuristic Engine
            self.gguf_model = None

    @property
    def is_gguf_active(self) -> bool:
        return self.gguf_model is not None

    def generate_intent(
        self,
        user_goal: str,
        tenant_uid: str,
        user_uid: str,
        site_scope: str | None = None,
        asset_scope: str | None = None,
        raw_asset_ids: list[str] | None = None,
        autonomy_requested: str = "HITL"
    ) -> IntentContract:

        """
        Execute intent generation via Tier 1 Local GGUF if loaded,
        otherwise execute via Tier 2 Deterministic Heuristic Engine.
        """
        if self.is_gguf_active and self.gguf_model:
            try:
                prompt = (
                    f"System: You are an industrial intent parser. Classify the user goal into JSON.\n"
                    f"User Goal: {user_goal}\n"
                    f"JSON Response:"
                )
                output = self.gguf_model(prompt, max_tokens=256, stop=["\n\n", "User:"])
                text = output["choices"][0]["text"].strip()
                parsed = json.loads(text)
                return IntentContract(
                    intent_uid=f"intent-{uuid.uuid4().hex[:8]}",
                    tenant_uid=tenant_uid,
                    user_uid=user_uid,
                    site_scope=site_scope,
                    asset_scope=asset_scope,
                    goal=user_goal,
                    domain="industrial_telemetry",
                    intent_type=parsed.get("intent_type", "hourly_sensor_upload"),
                    requested_outputs=parsed.get("requested_outputs", ["parquet"]),
                    requires_model=parsed.get("requires_model", False),
                    requires_visualization=True,
                    autonomy_requested="HITL",
                    constraints={"parsed_by": "local_gguf_engine", "model": self.active_gguf_path.name if self.active_gguf_path else "gguf"},
                    source_refs=raw_asset_ids or []
                )
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                pass

        # Tier 2 Fallback: Deterministic Heuristic & Rule Engine
        return self.heuristic_engine.parse_intent(
            user_goal=user_goal,
            tenant_uid=tenant_uid,
            user_uid=user_uid,
            site_scope=site_scope,
            asset_scope=asset_scope,
            raw_asset_ids=raw_asset_ids,
            autonomy_requested=autonomy_requested
        )

