"""
Shift state the central mutable state object for one play of THRESHOLD.

Tracks score, errors, rent, time, and a history of wrong verdicts used later
by the arrest sequence. Methods encapsulate state transitions so the game loop
tells the state what happened rather than mutating fields directly.

Companion class WrongVerdict is a small value object representing one mistake,
used by the Inspector's arrest speech.
"""

from core.clock import DEFAULT_SHIFT_DURATION_SECONDS
from exceptions import InvalidTravelerError


VALID_ACTIONS = {"approve", "deny", "detain"}

INITIAL_RENT = 10
INITIAL_TIME_SECONDS = DEFAULT_SHIFT_DURATION_SECONDS
TOTAL_TRAVELERS = 5
STREAK_TRIGGER_THRESHOLD = 3
TOTAL_ERROR_TRIGGER_THRESHOLD = 5
WRONG_VERDICT_RENT_COST = 1
WRONG_DETENTION_RENT_COST = 2
MORAL_VIOLATION_RENT_COST = 1
BRIBE_RENT_BONUS = 2
TIME_COST_PER_QUESTION = 15
TIME_COST_PER_NOTE_READ = 5


class WrongVerdict:
    """One recorded mistake used by Halmos's arrest speech."""

    def __init__(self, case_index, traveler_name, chosen_action, violation):
        if not isinstance(case_index, int) or isinstance(case_index, bool):
            raise InvalidTravelerError(
                f"case_index must be an int, got {type(case_index).__name__}"
            )
        if case_index < 1:
            raise InvalidTravelerError("case_index must be at least 1")

        if not isinstance(traveler_name, str) or not traveler_name.strip():
            raise InvalidTravelerError("traveler_name must be a non-empty string")

        if chosen_action not in VALID_ACTIONS:
            raise InvalidTravelerError(
                f"chosen_action must be one of {VALID_ACTIONS}, got '{chosen_action}'"
            )

        if not isinstance(violation, str) or not violation.strip():
            raise InvalidTravelerError("violation must be a non-empty string")

        self.case_index = case_index
        self.traveler_name = traveler_name.strip()
        self.chosen_action = chosen_action
        self.violation = violation.strip()

    def __repr__(self):
        return (
            f"WrongVerdict(case={self.case_index}, "
            f"name='{self.traveler_name}', action='{self.chosen_action}')"
        )


class ShiftState:
    """Central mutable state for one shift."""

    def __init__(self):
        self.current_traveler_index = 0
        self.score = 0
        self.rent = INITIAL_RENT
        self.consecutive_errors = 0
        self.total_errors = 0
        self.time_remaining_seconds = INITIAL_TIME_SECONDS
        self.wrong_verdicts = []
        self.accepted_bribe = False
        self.note_read = False
        self.current_interrogation = None

    
    # Predicates (state inspection)
    

    def should_trigger_review(self):
        """True if Internal Affairs should arrest the player now."""
        return (
            self.consecutive_errors >= STREAK_TRIGGER_THRESHOLD
            or self.total_errors >= TOTAL_ERROR_TRIGGER_THRESHOLD
        )

    def is_shift_complete(self):
        """True if all 5 travelers have been processed."""
        return self.current_traveler_index >= TOTAL_TRAVELERS

    def is_rent_depleted(self):
        """True if the family has been evicted."""
        return self.rent <= 0

    def remaining_travelers(self):
        """How many travelers are still in the queue."""
        return TOTAL_TRAVELERS - self.current_traveler_index

    
    # State transitions (mutate the state)


    def record_correct(self):
        """Player chose the correct verdict. Bump score, reset streak."""
        self.score += 1
        self.consecutive_errors = 0

    def record_wrong(self, case_index, traveler_name, chosen_action, violation):
        """Player chose the wrong verdict. Add to history, bump errors, deduct rent."""
        wrong = WrongVerdict(case_index, traveler_name, chosen_action, violation)
        self.wrong_verdicts.append(wrong)
        self.total_errors += 1
        self.consecutive_errors += 1
        cost = (
            WRONG_DETENTION_RENT_COST
            if chosen_action == "detain"
            else WRONG_VERDICT_RENT_COST
        )
        self.rent -= cost

    def record_moral_violation(self, case_index, traveler_name, violation):
        """Player approved the wounded refugee. Lighter rent cost than other errors."""
        wrong = WrongVerdict(case_index, traveler_name, "approve", violation)
        self.wrong_verdicts.append(wrong)
        self.total_errors += 1
        self.consecutive_errors += 1
        self.rent -= MORAL_VIOLATION_RENT_COST

    def record_bribe(self):
        """Player accepted the bribe. +2 rent, +1 score, flag for dark ending."""
        self.accepted_bribe = True
        self.rent += BRIBE_RENT_BONUS
        self.score += 1
        self.consecutive_errors = 0

    def consume_time(self, seconds):
        """Deduct time from the clock. Clamps at 0."""
        if not isinstance(seconds, int) or isinstance(seconds, bool):
            raise InvalidTravelerError(
                f"seconds must be an int, got {type(seconds).__name__}"
            )
        if seconds < 0:
            raise InvalidTravelerError("seconds cannot be negative")
        self.time_remaining_seconds = max(0, self.time_remaining_seconds - seconds)

    def advance_traveler(self):
        """Move to the next traveler. Clears the interrogation session."""
        self.current_traveler_index += 1
        self.current_interrogation = None

    def mark_note_read(self):
        """Player read the note between travelers 1 and 2."""
        self.note_read = True
        self.consume_time(TIME_COST_PER_NOTE_READ)

    def __repr__(self):
        return (
            f"ShiftState(traveler={self.current_traveler_index}/{TOTAL_TRAVELERS}, "
            f"score={self.score}, rent={self.rent}, "
            f"errors={self.total_errors}, streak={self.consecutive_errors})"
        )


    