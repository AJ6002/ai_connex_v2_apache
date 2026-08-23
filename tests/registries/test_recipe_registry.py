"""
Unit tests for Task 1.2.3 Recipe Registry contract binding & startup safety validation.
"""

import pytest
from pydantic import ValidationError
from contracts.recipe.recipe_contract import RecipeContract
from registries.recipes.loader import load_and_validate_recipes


def test_recipe_registry_load_and_validate_success():
    """Verify prepare_recipes.json loads successfully into typed RecipeContract objects with safety flags."""
    recipes = load_and_validate_recipes()
    assert len(recipes) >= 2
    for recipe in recipes:
        assert isinstance(recipe, RecipeContract)
        assert hasattr(recipe, "destructive_operations")
        assert recipe.destructive_operations is False
        assert hasattr(recipe, "inputs")
        assert hasattr(recipe, "outputs")


def test_recipe_missing_safety_flag_fails_startup():
    """Verify Task 1.2.3 requirement: A recipe missing the destructive_operations safety flag fails startup/validation."""
    invalid_recipe_data = {
        "recipe_id": "recipe_unsafe_v1",
        "recipe_name": "Unsafe Recipe Without Safety Flag",
        "domain": "industrial_telemetry",
        "target_task": "test_task",
        "steps": []
        # Missing destructive_operations: false
    }

    with pytest.raises(ValidationError):
        RecipeContract.model_validate(invalid_recipe_data)
