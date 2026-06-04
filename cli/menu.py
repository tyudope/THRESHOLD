# cli/menu.py
"""
Main game loop for THRESHOLD.

run_game() is the single entry point. It wires together the catalog (content),
the shift state (mutable game state), the real-time clock, and the rendering
layer in cli/ui.py. This module owns all flow control and player input; it
delegates every pixel of output to ui.py and every rule to core/.

Control flow uses two project exceptions as signals:
  ShiftExpiredError    — the clock hit zero mid-action
  ReviewTriggeredError — Internal Affairs intervened (3 streak / 5 total errors)
Both are caught at the top of run_game() and routed to the end-of-shift screen.
"""

import time

from cli import theme, ui
from cli.decorators import log_action
from core.catalog import Catalog
from core.clock import ShiftClock
from core.internal_affairs import ENDING_ARRESTED
from core.lie_detector import detect_contradictions
from core.verdict import compute_shift_result
from exceptions import ReviewTriggeredError, ShiftExpiredError, ThresholdError
from models.interrogation import InterrogationSession
from models.shift import (
    ShiftState,
    TIME_COST_PER_NOTE_READ,
    TIME_COST_PER_QUESTION,
    TOTAL_TRAVELERS,
)

# How long a verdict banner lingers before the next traveler.
FEEDBACK_PAUSE_SECONDS = 2.0
NOTE_PAUSE_SECONDS = 2.5


# Screen composition helpers

def _render_case_screen(state, clock, ruleset, traveler, case_number):
    """Clear and draw the full booth view: directives, stats, card, actions."""
    theme.clear_screen()
    ui.render_directives(ruleset)
    ui.render_stats_bar(state, clock)
    ui.render_traveler_card(traveler, case_number, TOTAL_TRAVELERS)
    ui.render_action_menu()


def _handle_note(state, clock, dialogue):
    """Show the note interstitial before traveler 2 and apply the choice."""
    ui.render_note_interstitial(dialogue)
    choice = input("> ").strip().upper()
    if choice == "R":
        state.mark_note_read()
        clock.consume(TIME_COST_PER_NOTE_READ)
        ui.render_note_content(dialogue)
        time.sleep(NOTE_PAUSE_SECONDS)


# Verdict resolution

def _resolve_verdict(state, traveler, case_number, action):
    """
    Record the player's verdict and render its feedback.

    The moral case is special: approving the wounded Hawkmoor resident is the
    documented violation, so it routes to record_moral_violation rather than
    the ordinary wrong-verdict path.
    """
    name = traveler.document.name

    if action == "approve" and traveler.is_moral_case and traveler.correct_verdict == "deny":
        state.record_moral_violation(
            case_number,
            name,
            "Approved a Hawkmoor resident in violation of Directive 03.",
        )
        ui.render_moral_choice_feedback(traveler.reason)
    elif action == traveler.correct_verdict:
        state.record_correct()
        ui.render_verdict_feedback(
            correct=True, reason=traveler.reason, action=action, rent_change=0
        )
    else:
        violation = traveler.reason.split(".")[0] + "."
        state.record_wrong(case_number, name, action, violation)
        rent_change = -2 if action == "detain" else -1
        ui.render_verdict_feedback(
            correct=False, reason=traveler.reason, action=action, rent_change=rent_change
        )


# Interrogation sub-flow

def _run_interrogation(state, clock, traveler):
    """
    Drive the question-selection loop.

    Returns "bribe" if the player accepted a bribe (the case is over and the
    caller should advance the traveler), or "back" to return to the actions.
    """
    if state.current_interrogation is None:
        state.current_interrogation = InterrogationSession(
            traveler.questions,
            max_questions=2,
            time_cost_per_question=TIME_COST_PER_QUESTION,
        )
    session = state.current_interrogation

    while True:
        ui.render_interrogation_menu(session, traveler)
        choice = input("> ").strip().upper()

        if choice == "B":
            return "back"

        if not choice.isdigit():
            ui.render_error_message("Pick a question number or [B] to go back.")
            time.sleep(1.0)
            continue

        index = int(choice) - 1
        if index < 0 or index >= len(session.available_questions):
            ui.render_error_message("No question with that number.")
            time.sleep(1.0)
            continue

        if index in session.asked_indices:
            ui.render_error_message("You already asked that question.")
            time.sleep(1.0)
            continue

        if not session.can_ask_more():
            print(theme.colored("  No questions left in this interrogation.", theme.GRAY))
            time.sleep(1.0)
            continue

        # Spend the question and its time on both the state and the live clock.
        question = session.ask(index)
        state.consume_time(TIME_COST_PER_QUESTION)
        clock.consume(TIME_COST_PER_QUESTION)

        contradictions = detect_contradictions(question.answer_text, traveler)
        contradiction_text = contradictions[0][1] if contradictions else None
        ui.render_question_answer(traveler, question, contradiction_text=contradiction_text)

        if question.is_bribe_offer:
            answer = input("> ").strip().upper()
            if answer == "Y":
                state.record_bribe()
                ui.render_bribe_taken_feedback()
                time.sleep(FEEDBACK_PAUSE_SECONDS)
                return "bribe"
            # Refused — the traveler stays; continue interrogating or verdict.

        if not session.can_ask_more():
            print(theme.colored("  That was your last question. [B] to decide.", theme.GRAY))
        time.sleep(1.0)


# One traveler, start to finish

def _play_case(state, clock, ruleset, traveler, case_number):
    """
    Run a single traveler's booth interaction until a verdict is reached.

    Raises ReviewTriggeredError if the verdict pushes the player over the
    Internal Affairs threshold.
    """
    while True:
        _render_case_screen(state, clock, ruleset, traveler, case_number)
        choice = input("> ").strip().upper()
        clock.raise_if_expired()

        match choice:
            case "I":
                outcome = _run_interrogation(state, clock, traveler)
                clock.raise_if_expired()
                if outcome == "bribe":
                    state.advance_traveler()
                    return
                # "back" — redraw the action screen on the next loop.

            case "A" | "D" | "X":
                action = {"A": "approve", "D": "deny", "X": "detain"}[choice]
                _resolve_verdict(state, traveler, case_number, action)
                time.sleep(FEEDBACK_PAUSE_SECONDS)
                state.advance_traveler()
                if state.should_trigger_review():
                    raise ReviewTriggeredError("Internal Affairs has flagged the booth.")
                return

            case _:
                ui.render_error_message("Unknown command. Use I / A / D / X.")
                time.sleep(1.0)


# Entry point

@log_action
def run_game():
    """Play one full shift of THRESHOLD."""
    ui.render_title_screen()
    input()

    try:
        catalog = Catalog.load_default()
    except ThresholdError as exc:
        theme.clear_screen()
        ui.render_error_message(f"Could not load game content: {exc}")
        return

    state = ShiftState()
    clock = ShiftClock()

    theme.clear_screen()
    ui.render_directives(catalog.ruleset)
    print()
    print(theme.dim("Press Enter to start your shift.".center(ui.WIDTH)))
    input()

    clock.start()
    review_triggered = False

    try:
        for case_number in range(1, TOTAL_TRAVELERS + 1):
            traveler = catalog.travelers[case_number - 1]

            if case_number == 2 and not state.note_read:
                _handle_note(state, clock, catalog.dialogue)

            _play_case(state, clock, catalog.ruleset, traveler, case_number)
            clock.raise_if_expired()

    except ReviewTriggeredError:
        review_triggered = True
    except ShiftExpiredError:
        pass
    except ThresholdError as exc:
        clock.stop()
        theme.clear_screen()
        ui.render_error_message(str(exc))
        return

    clock.stop()

    result = compute_shift_result(state, review_triggered=review_triggered)

    if result.ending_key == ENDING_ARRESTED:
        ui.render_arrest_sequence(state, catalog.dialogue)
        input()

    ui.render_ending(result, catalog.dialogue)
    input()


if __name__ == "__main__":
    run_game()
