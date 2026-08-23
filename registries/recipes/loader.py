"""
Recipe Registry Loader & Validator.
Loads prepare_recipes.json and validates each entry against RecipeContract at startup.
Fails loudly if destructive_operations safety flag or required contract fields are missing.
"""

import json
from pathlib import Path
from typing import List, Optional

from contracts.recipe.recipe_contract import RecipeContract


def load_and_validate_recipes(recipes_json_path: Optional[Path] = None) -> List[RecipeContract]:
    """
    Load and validate recipes from JSON file against RecipeContract.
    Raises pydantic.ValidationError if any recipe lacks destructive_operations flag or valid contract shape.
    """
    if recipes_json_path is None:
        recipes_json_path = Path(__file__).resolve().parent / "prepare_recipes.json"

    with open(recipes_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    recipe_entries = data.get("recipes", [])
    validated_recipes = []

    for entry in recipe_entries:
        recipe = RecipeContract.model_validate(entry)
        validated_recipes.append(recipe)

    return validated_recipes
