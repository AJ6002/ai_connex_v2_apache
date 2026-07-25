"""
intent/prompter.py - Responsive Terminal Prompter (Plain ASCII)
=================================================================
Displays DatasetCard + IntentOptions in a plain ASCII-bordered terminal box,
halts execution waiting for user input, and handles non-interactive fallback.

Features:
  - Plain ASCII box borders (no Unicode/box-drawing/emoji - safe on any
    terminal, locale, or CI log encoding)
  - Halts terminal for user input (input())
  - Explicit batch mode: --batch always skips prompting, regardless of tty state
  - Non-interactive fallback: auto-selects default option when stdin is not a tty
  - Supports --strategy CLI override (bypasses prompt entirely)
"""

from __future__ import annotations

import sys
from typing import List, Optional

from .models import DatasetCard, IntentOption


def _box_line(text: str, width: int) -> str:
    """Format a line inside a box with padding."""
    padded = f" {text}"
    return f"|{padded:<{width}}|"


def _horizontal_rule(width: int, left: str = "+", right: str = "+") -> str:
    return f"{left}{'-' * width}{right}"


class TerminalPrompter:
    """
    Terminal Prompter that displays DatasetCard and IntentOptions,
    halts terminal for user selection, and returns the chosen option_id.

    Parameters
    ----------
    force_interactive : bool
        If True, always shows the interactive prompt even if stdin is not a tty.
    force_batch : bool
        If True, always skips the prompt and auto-selects the default option,
        regardless of tty state. Takes precedence over force_interactive.
    """

    def __init__(self, force_interactive: bool = False, force_batch: bool = False):
        self.force_interactive = force_interactive
        self.force_batch = force_batch

    def prompt(
        self,
        card: DatasetCard,
        options: List[IntentOption],
        strategy_override: Optional[str] = None,
        question: Optional[str] = None,
    ) -> str:
        """
        Display prompt and return the selected option_id.

        Parameters
        ----------
        card : DatasetCard
            Dataset summary to display.
        options : List[IntentOption]
            Choices to present.
        strategy_override : str, optional
            If set, bypasses the prompt entirely and returns this option_id.
            If the override does not match any known option, falls back to
            the default option and logs a warning (fail-visible, not silent).
        question : str, optional
            The question text to display. When the intelligence layer is active
            this is LLM-generated per dataset; falls back to a generic prompt.

        Returns
        -------
        str
            The selected option_id.
        """
        if not options:
            return "auto_model"

        # Bypass 1: Strategy override from CLI --strategy flag.
        # Resolution order: exact option_id -> output_mode alias -> 1-based index.
        # option_ids are LLM-generated and vary between runs, so output_mode and
        # index are the stable selectors for automation.
        if strategy_override:
            resolved = self._resolve_override(strategy_override, options)
            if resolved is not None:
                return resolved

            default = self._get_default(options)
            valid_ids = ", ".join(o.option_id for o in options)
            valid_modes = ", ".join(sorted({o.output_mode for o in options if o.output_mode}))
            print(
                f"\n[WARNING] Strategy '{strategy_override}' is not valid for this dataset.\n"
                f"          Valid option ids   : {valid_ids}\n"
                + (f"          Valid output modes : {valid_modes}\n" if valid_modes else "")
                + f"          Valid indices      : 1-{len(options)}\n"
                f"          Falling back to default: '{default}'\n"
            )
            return default

        # Bypass 2: Explicit batch mode - always skip prompting
        if self.force_batch:
            default = self._get_default(options)
            self._print_non_interactive_notice(card, default)
            return default

        # Bypass 3: Non-interactive terminal (CI, pipe) unless interactive is forced
        if not self._is_interactive():
            default = self._get_default(options)
            self._print_non_interactive_notice(card, default)
            return default

        # Bypass 4: Only one option - no choice needed
        if len(options) <= 1:
            self._print_auto_proceed(card, options[0])
            return options[0].option_id

        # Full interactive prompt
        return self._interactive_prompt(card, options, question)

    def _interactive_prompt(
        self,
        card: DatasetCard,
        options: List[IntentOption],
        question: Optional[str] = None,
    ) -> str:
        """Render the full prompt box and wait for user input."""
        width = 75

        # Print DatasetCard box
        print()
        print(_horizontal_rule(width))
        print(_box_line(f"DATASET CARD - {card.dataset_name}", width))
        print(_horizontal_rule(width, "+", "+"))
        print(_box_line(f"Domain     : {card.domain.replace('_', ' ').title()}", width))
        print(_box_line(f"Structure  : {card.summary}", width))

        if card.entity_keys:
            print(_box_line(f"Entity Keys: {', '.join(card.entity_keys)}", width))
        if card.time_keys:
            print(_box_line(f"Time Keys  : {', '.join(card.time_keys)}", width))

        print(_horizontal_rule(width, "+", "+"))
        print()

        # Print question (LLM-generated when available, else generic fallback)
        print(question or "What do you want the model to do?")
        print()

        # Print options
        for idx, opt in enumerate(options, 1):
            default_tag = " (default)" if opt.is_default else ""
            print(f"  [{idx}] {opt.label}{default_tag}")
            print(f"       {opt.description}")
            print()

        # Input loop
        while True:
            try:
                raw = input(f"Enter choice [1-{len(options)}]: ").strip()
                if not raw:
                    # Enter with no input = default
                    default = self._get_default(options)
                    print(f"\n[Using default: {self._label_for(options, default)}]\n")
                    return default
                choice_num = int(raw)
                if 1 <= choice_num <= len(options):
                    selected = options[choice_num - 1]
                    print(f"\nSelected: {selected.label}\n")
                    return selected.option_id
                else:
                    print(f"  Please enter a number between 1 and {len(options)}.")
            except ValueError:
                # Maybe they typed the option_id directly
                matching = [o for o in options if o.option_id == raw]
                if matching:
                    print(f"\nSelected: {matching[0].label}\n")
                    return matching[0].option_id
                print(f"  Invalid input. Enter a number [1-{len(options)}].")
            except (EOFError, KeyboardInterrupt):
                default = self._get_default(options)
                print(f"\n[Interrupted - using default: {self._label_for(options, default)}]\n")
                return default

    def _print_non_interactive_notice(self, card: DatasetCard, default_id: str) -> None:
        """Print notice when running in non-interactive/batch mode."""
        print(f"\nDataset: {card.dataset_name} ({card.summary})")
        print(f"  -> Non-interactive mode: auto-selecting '{default_id}'")
        print()

    def _print_auto_proceed(self, card: DatasetCard, option: IntentOption) -> None:
        """Print notice when only one option is feasible (no halt needed)."""
        print(f"\nDataset: {card.dataset_name}")
        print(f"  {card.summary}")
        print(f"  -> Proceeding with: {option.label}")
        print()

    def _is_interactive(self) -> bool:
        """Check if stdin is attached to a real terminal."""
        if self.force_interactive:
            return True
        return hasattr(sys.stdin, "isatty") and sys.stdin.isatty()

    @staticmethod
    def _resolve_override(override: str, options: List[IntentOption]) -> Optional[str]:
        """
        Resolve a --strategy value against the available options.

        Accepts, in priority order:
          1. An exact option_id
          2. An output_mode value (stable across runs, unlike LLM option_ids)
          3. A 1-based index into the presented options
        Returns None when nothing matches.
        """
        candidate = override.strip()

        for option in options:
            if option.option_id == candidate:
                return option.option_id

        mode_matches = [o for o in options if o.output_mode and o.output_mode == candidate]
        if mode_matches:
            # Prefer the recommended option when several share an output_mode
            preferred = next((o for o in mode_matches if o.is_default), mode_matches[0])
            return preferred.option_id

        if candidate.isdigit():
            index = int(candidate)
            if 1 <= index <= len(options):
                return options[index - 1].option_id

        return None

    @staticmethod
    def _get_default(options: List[IntentOption]) -> str:
        """Return the default option_id (first with is_default=True, or first overall)."""
        for opt in options:
            if opt.is_default:
                return opt.option_id
        return options[0].option_id if options else "auto_model"

    @staticmethod
    def _label_for(options: List[IntentOption], option_id: str) -> str:
        """Look up the human label for an option_id (for interrupt/default messages)."""
        for opt in options:
            if opt.option_id == option_id:
                return opt.label
        return option_id
