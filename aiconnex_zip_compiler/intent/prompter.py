"""
intent/prompter.py — Responsive TUI Terminal Prompter
======================================================
Displays DatasetCard + IntentOptions in a clean ANSI-styled terminal box,
halts execution waiting for user input, and handles non-interactive fallback.

Features:
  - Rich visual box with ANSI borders (works on Windows 10+ and Unix)
  - Halts terminal for user input (sys.stdin.readline)
  - Non-interactive fallback: auto-selects default option when stdin is not a tty
  - Supports --strategy CLI override (bypasses TUI entirely)
"""

from __future__ import annotations

import sys
from typing import List, Optional

from .models import DatasetCard, IntentOption


# ANSI box-drawing characters (works on modern terminals)
BOX_TL = "┌"
BOX_TR = "┐"
BOX_BL = "└"
BOX_BR = "┘"
BOX_H = "─"
BOX_V = "│"
BOX_ML = "├"
BOX_MR = "┤"

# ANSI color codes (optional, degrade gracefully)
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def _box_line(text: str, width: int) -> str:
    """Format a line inside a box with padding."""
    padded = f" {text}"
    return f"{BOX_V}{padded:<{width}}{BOX_V}"


def _horizontal_rule(width: int, left: str = BOX_TL, right: str = BOX_TR) -> str:
    return f"{left}{BOX_H * width}{right}"


class TerminalPrompter:
    """
    TUI Prompter that displays DatasetCard and IntentOptions,
    halts terminal for user selection, and returns the chosen option_id.
    """

    def __init__(self, force_interactive: bool = False):
        self.force_interactive = force_interactive

    def prompt(
        self,
        card: DatasetCard,
        options: List[IntentOption],
        strategy_override: Optional[str] = None,
    ) -> str:
        """
        Display TUI and return the selected option_id.

        Parameters
        ----------
        card : DatasetCard
            Dataset summary to display.
        options : List[IntentOption]
            Choices to present.
        strategy_override : str, optional
            If set, bypasses TUI entirely and returns this option_id.

        Returns
        -------
        str
            The selected option_id.
        """
        # Bypass 1: Strategy override from CLI --strategy flag
        if strategy_override:
            matching = [o for o in options if o.option_id == strategy_override]
            if matching:
                return matching[0].option_id
            # If override doesn't match any option, use default
            return self._get_default(options)

        # Bypass 2: Non-interactive terminal (CI, pipe, batch)
        if not self._is_interactive():
            default = self._get_default(options)
            self._print_non_interactive_notice(card, default)
            return default

        # Bypass 3: Only one option — no choice needed
        if len(options) <= 1:
            self._print_auto_proceed(card, options[0] if options else None)
            return options[0].option_id if options else "auto_model"

        # Full TUI display
        return self._interactive_prompt(card, options)

    def _interactive_prompt(self, card: DatasetCard, options: List[IntentOption]) -> str:
        """Render full TUI box and wait for user input."""
        width = 75

        # Print DatasetCard box
        print()
        print(_horizontal_rule(width))
        print(_box_line(f"📊 {BOLD}DATASET CARD{RESET} — {card.dataset_name}", width))
        print(_horizontal_rule(width, BOX_ML, BOX_MR))
        print(_box_line(f"Domain     : {card.domain.replace('_', ' ').title()}", width))
        print(_box_line(f"Structure  : {card.summary}", width))

        if card.entity_keys:
            print(_box_line(f"Entity Keys: {', '.join(card.entity_keys)}", width))
        if card.time_keys:
            print(_box_line(f"Time Keys  : {', '.join(card.time_keys)}", width))

        print(_horizontal_rule(width, BOX_BL, BOX_BR))
        print()

        # Print question
        print(f"{BOLD}What do you want the model to do?{RESET}")
        print()

        # Print options
        for idx, opt in enumerate(options, 1):
            icon = opt.icon + " " if opt.icon else ""
            default_tag = f" {DIM}(default){RESET}" if opt.is_default else ""
            print(f"  [{idx}] {icon}{BOLD}{opt.label}{RESET}{default_tag}")
            print(f"       {DIM}{opt.description}{RESET}")
            print()

        # Input loop
        while True:
            try:
                raw = input(f"Enter choice [1-{len(options)}]: ").strip()
                if not raw:
                    # Enter with no input = default
                    return self._get_default(options)
                choice_num = int(raw)
                if 1 <= choice_num <= len(options):
                    selected = options[choice_num - 1]
                    print(f"\n{GREEN}✓ Selected: {selected.label}{RESET}\n")
                    return selected.option_id
                else:
                    print(f"  Please enter a number between 1 and {len(options)}.")
            except ValueError:
                # Maybe they typed the option_id directly
                matching = [o for o in options if o.option_id == raw]
                if matching:
                    print(f"\n{GREEN}✓ Selected: {matching[0].label}{RESET}\n")
                    return matching[0].option_id
                print(f"  Invalid input. Enter a number [1-{len(options)}].")
            except (EOFError, KeyboardInterrupt):
                print(f"\n{YELLOW}⚠ Interrupted — using default option.{RESET}\n")
                return self._get_default(options)

    def _print_non_interactive_notice(self, card: DatasetCard, default_id: str) -> None:
        """Print notice when running in non-interactive mode."""
        print(f"\n📊 Dataset: {card.dataset_name} ({card.summary})")
        print(f"   → Non-interactive mode: auto-selecting '{default_id}'")
        print()

    def _print_auto_proceed(self, card: DatasetCard, option: Optional[IntentOption]) -> None:
        """Print notice when only one option is feasible (no halt needed)."""
        print(f"\n📊 Dataset: {card.dataset_name}")
        print(f"   {card.summary}")
        if option:
            print(f"   → Proceeding with: {option.label}")
        print()

    def _is_interactive(self) -> bool:
        """Check if stdin is attached to a real terminal."""
        if self.force_interactive:
            return True
        return hasattr(sys.stdin, "isatty") and sys.stdin.isatty()

    @staticmethod
    def _get_default(options: List[IntentOption]) -> str:
        """Return the default option_id (first with is_default=True, or first overall)."""
        for opt in options:
            if opt.is_default:
                return opt.option_id
        return options[0].option_id if options else "auto_model"
