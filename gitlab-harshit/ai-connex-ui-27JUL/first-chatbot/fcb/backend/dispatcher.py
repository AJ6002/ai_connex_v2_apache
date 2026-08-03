"""
Dispatcher: given a validated ExtractedIntent, either answers directly
(read-only intents) or triggers the corresponding pipeline stage
(low/high-impact intents), and returns the reply text plus the badge flags
the frontend's MainChatView.tsx expects
(topologyAssigned / dagMatched / recipeCompiled).
"""

from schemas import ExtractedIntent
import pipeline_state as ps


def _badges_for(dataset_id: str | None) -> dict:
    if not dataset_id:
        return {"topologyAssigned": False, "dagMatched": False, "recipeCompiled": False}
    state = ps.get_dataset_state(dataset_id) or {}
    return {
        "topologyAssigned": bool(state.get("profiled")),
        "dagMatched": bool(state.get("dag_verified")),
        "recipeCompiled": bool(state.get("recipe_compiled")),
    }


def dispatch(extracted: ExtractedIntent) -> dict:
    intent = extracted.intent
    entities = extracted.entities
    dataset_id = entities.dataset_id

    if intent == "greeting":
        return {"reply": "Hello! I'm the AI Connexx assistant. What would you like to do with your dataset today?",
                **_badges_for(dataset_id)}

    if intent == "general_help":
        return {"reply": (
            "I can help you profile a dataset, run DAG verification, compile a training "
            "recipe, check status at any stage, or deploy a finished pipeline."
        ), **_badges_for(dataset_id)}

    if intent == "out_of_scope":
        return {"reply": "That's outside what I can help with here -- I handle dataset profiling, "
                          "DAG verification, recipe compilation, and deployment for AI Connexx.",
                **_badges_for(dataset_id)}

    if intent == "get_dataset_status":
        state = ps.get_dataset_state(dataset_id) or {}
        reply = (
            f"Dataset '{dataset_id}': profiled={state.get('profiled')}, "
            f"DAG matched={state.get('dag_matched')}, recipe compiled={state.get('recipe_compiled')}."
        )
        return {"reply": reply, **_badges_for(dataset_id)}

    if intent == "run_dataset_profiling":
        # TODO: replace with a real call into the Dataset Profiler (meta1) service
        ps.mark_stage_complete(dataset_id, "profiled", profiled=True, algorithm_family="regression")
        return {"reply": f"Profiling complete for '{dataset_id}'. Recommended algorithm family: regression.",
                **_badges_for(dataset_id)}

    if intent == "get_dag_status":
        state = ps.get_dataset_state(dataset_id) or {}
        reply = f"DAG for '{dataset_id}': matched={state.get('dag_matched')}, verified={state.get('dag_verified')}."
        return {"reply": reply, **_badges_for(dataset_id)}

    if intent == "run_dag_verification":
        # TODO: replace with a real call into the DAG Execution (meta2) service
        ps.mark_stage_complete(dataset_id, "dag_verified", dag_verified=True, dag_matched="DAG-91B-A")
        return {"reply": f"DAG verification complete for '{dataset_id}' -- matched schema DAG-91B-A.",
                **_badges_for(dataset_id)}

    if intent == "get_recipe_status":
        state = ps.get_dataset_state(dataset_id) or {}
        return {"reply": f"Recipe for '{dataset_id}': compiled={state.get('recipe_compiled')}.",
                **_badges_for(dataset_id)}

    if intent == "compile_training_recipe":
        # TODO: replace with a real call into the Recipe Orchestrator (meta3) service
        ps.mark_stage_complete(dataset_id, "recipe_compiled", recipe_compiled=True)
        return {"reply": f"Training recipe compiled for '{dataset_id}'.", **_badges_for(dataset_id)}

    if intent == "deploy_pipeline":
        # High-impact -- the route layer only reaches here after explicit confirmation
        # TODO: replace with a real deployment trigger
        return {"reply": f"Deployment initiated for '{dataset_id}'.", **_badges_for(dataset_id)}

    # Should not normally be reached -- unknown intents are coerced to out_of_scope upstream
    return {"reply": "I wasn't able to determine what you'd like to do.", **_badges_for(dataset_id)}
