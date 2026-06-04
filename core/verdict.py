# core/verdict.py
"""
End-of-shift scoring and result summarization.

Takes the final ShiftState after all travelers have been processed (or
after an arrest trigger) and produces a structured ShiftResult — the
single object the CLI needs to render the ending screen.

This module is pure query: it reads state, it doesn't mutate it. The
mutation side lives on ShiftState itself.
"""

from models.shift import ShiftState, TOTAL_TRAVELERS
from core.internal_affairs import select_ending

# Result container

class ShiftResult:
    """The final summary of one shift — used by the CLI to render the ending."""

    def __init__(
        self,
        score,
        total_travelers,
        rent_remaining,
        total_errors,
        accuracy_pct,
        ending_key,
        accepted_bribe,
        note_read,
        wrong_verdicts,
    ):
        self.score = score
        self.total_travelers = total_travelers
        self.rent_remaining = rent_remaining
        self.total_errors = total_errors
        self.accuracy_pct = accuracy_pct
        self.ending_key = ending_key
        self.accepted_bribe = accepted_bribe
        self.note_read = note_read
        self.wrong_verdicts = list(wrong_verdicts)    # defensive copy

    def __repr__(self):
        return (
            f"ShiftResult(score={self.score}/{self.total_travelers}, "
            f"rent={self.rent_remaining}, "
            f"ending='{self.ending_key}', "
            f"accuracy={self.accuracy_pct}%)"
        )


# Helpers

def accuracy_percentage(state):
    """
    Return the accuracy as an integer percentage (0–100).

    Computed as score / processed_count. If no travelers were processed,
    returns 0 to avoid division by zero.
    """
    if not isinstance(state, ShiftState):
        raise TypeError(
            f"state must be a ShiftState instance, got {type(state).__name__}"
        )
    processed = state.current_traveler_index
    if processed == 0:
        return 0
    return int((state.score / processed) * 100)


def format_wrong_verdicts(state):
    """
    Return a sorted list of formatted strings describing each wrong verdict.

    Wrong verdicts are sorted by case_index so they read out in chronological
    order, matching how Halmos's speech presents them.

    Uses a lambda to extract the sort key — a textbook use of functions
    as first-class values.
    """
    if not isinstance(state, ShiftState):
        raise TypeError(
            f"state must be a ShiftState instance, got {type(state).__name__}"
        )

    sorted_wrongs = sorted(state.wrong_verdicts, key=lambda w: w.case_index)

    return [
        f"#{w.case_index} — {w.traveler_name}: {w.violation}"
        for w in sorted_wrongs
    ]


# Main entry — build a ShiftResult from the final state

def compute_shift_result(state, review_triggered=False):
    """
    Build a ShiftResult summarizing this shift.

    Args:
        state:            final ShiftState
        review_triggered: True if Internal Affairs intervened during the shift

    Returns:
        ShiftResult
    """
    if not isinstance(state, ShiftState):
        raise TypeError(
            f"state must be a ShiftState instance, got {type(state).__name__}"
        )
    if not isinstance(review_triggered, bool):
        raise TypeError("review_triggered must be a bool")

    return ShiftResult(
        score=state.score,
        total_travelers=TOTAL_TRAVELERS,
        rent_remaining=state.rent,
        total_errors=state.total_errors,
        accuracy_pct=accuracy_percentage(state),
        ending_key=select_ending(state, review_triggered=review_triggered),
        accepted_bribe=state.accepted_bribe,
        note_read=state.note_read,
        wrong_verdicts=state.wrong_verdicts,
    )