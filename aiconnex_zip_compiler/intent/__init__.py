"""
aiconnex_zip_compiler.intent - HITL Intent & Dataset Card Layer
================================================================
Provides the interactive Terminal UI (TUI) that:
  1. Generates a DatasetCard (lightweight pre-pipeline inspection)
  2. Classifies feasible modeling directions
  3. Prompts the user for their intent (plain language, no ML jargon)
  4. Resolves the choice into a CompilationStrategy for the plugin pipeline
"""

from .models import DatasetCard, IntentOption, CompilationStrategy, IntentDecision
from .card_generator import CardGenerator
from .classifier import IntentClassifier
from .resolver import IntentResolver
from .prompter import TerminalPrompter

__all__ = [
    "DatasetCard",
    "IntentOption",
    "CompilationStrategy",
    "IntentDecision",
    "CardGenerator",
    "IntentClassifier",
    "IntentResolver",
    "TerminalPrompter",
]
