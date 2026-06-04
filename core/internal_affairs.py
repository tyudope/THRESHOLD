# core/internal_affairs.py
"""
Internal Affairs handles arrest triggering and the role-reversal sequence.

This module owns the dramatic core of the game: when the player fails
(3 consecutive errors OR 5 total), Inspector Halmos arrives, reads the
specific wrong verdicts aloud, and the player must ACCEPT THEIR FATE.

The speech is exposed as a generator so the CLI can pace each line
independently perfect pairing with the @reveal_slowly decorator.
"""

from models.shift import ShiftState


# Ending identifiers used to look up text from data/inspector_dialogue.json
ENDING_PROMOTED_CLEAN = "promoted_clean"
ENDING_PROMOTED_DARK = "promoted_dark"
ENDING_CONTINUE_SHIFT = "continue_shift"
ENDING_ARRESTED = "arrested"


# Trigger detection

def should_trigger_review(state):
    """
    Returns True if Internal Affairs should arrest the player now.
    """
    if not isinstance(state, ShiftState):
        raise TypeError(
            f"state must be a ShiftState instance, got {type(state).__name__}"
        )
    return state.should_trigger_review()



# Halmos's speech the generator

def generate_review_speech(state, dialogue):
    """
    Yield the Inspector's arrest speech line by line.
    """
    if not isinstance(state, ShiftState):
        raise TypeError(
            f"state must be a ShiftState instance, got {type(state).__name__}"
        )
    if not isinstance(dialogue, dict):
        raise TypeError(
            f"dialogue must be a dict, got {type(dialogue).__name__}"
        )

    # Opening
    yield "Inspector Selim-X."
    yield ""

    # Reason for the review - match-case routes the trigger type
    arrest_intro = dialogue["arrest_intro"]
    if state.consecutive_errors >= 3:
        yield arrest_intro["streak_trigger"]
    else:
        yield arrest_intro["total_trigger"]
    yield ""

    # Read out every wrong verdict by case number and traveler name
    for wrong in state.wrong_verdicts:
        yield (
            f"Traveler #{wrong.case_index} - {wrong.traveler_name}. "
            f"{wrong.violation}"
        )

    yield ""

    for verdict_line in dialogue["arrest_verdict"]:
        yield verdict_line

    yield ""

    # The note callback different depending on whether the player read it
    note_callback = dialogue["arrest_note_callback"]
    if state.note_read:
        yield note_callback["note_read"]
    else:
        yield note_callback["note_ignored"]


# Ending selection pure function

def select_ending(state, review_triggered=False):
    """
    Determine which ending text to use based on the final shift state.
    """
    if not isinstance(state, ShiftState):
        raise TypeError(
            f"state must be a ShiftState instance, got {type(state).__name__}"
        )
    if not isinstance(review_triggered, bool):
        raise TypeError("review_triggered must be a bool")

    # Arrest takes precedence over everything else
    if review_triggered or state.should_trigger_review():
        return ENDING_ARRESTED

    # Rent depleted is also an arrest (different narrative but same screen)
    if state.is_rent_depleted():
        return ENDING_ARRESTED

    # Final-tally arrest: less than 3 correct
    if state.score < 3:
        return ENDING_ARRESTED

    # Promoted: perfect score
    if state.score >= 5:
        if state.accepted_bribe:
            return ENDING_PROMOTED_DARK
        return ENDING_PROMOTED_CLEAN

    # Middle ground: 3 or 4 correct
    return ENDING_CONTINUE_SHIFT

# Convenience function: speech as a list (for testing / non-streaming UIs)


def collect_review_speech(state, dialogue):
    """
    Materialize the generator into a list - useful for tests or
    non-streaming UIs that want all lines at once.
    Demonstrates the same generator above, consumed eagerly.
    """
    return list(generate_review_speech(state, dialogue))