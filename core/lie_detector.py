# core/lie_detector.py
"""
Interrogation evidence engine  cross-references answers against documents
using regex pattern matching.

The validator handles document-only rules (approve/deny). This module
handles the harder case: did the traveler's interrogation answers
contradict their own paperwork or the world's facts?

Used by the game loop to decide whether a 'detain' verdict is warranted.
"""

import re

from models.traveler import Traveler
from models.interrogation import Question


# Compiled regex patterns — compiled once at module load

# Neural ID format: NID-XXXX-X-XXXX-XX where X is alphanumeric
# Example: NID-7741-X-44A2-9F
NEURAL_ID_PATTERN = re.compile(r"^NID-\d{4}-[A-Z]-[A-Z0-9]{4}-[A-Z0-9]{2}$")

# Patterns for forbidden/fictional things mentioned in answers
# These represent claims that contradict the world's facts
FORBIDDEN_LOCATION_PATTERNS = {
    "docks_dont_exist": re.compile(
        r"\b(docks?|harbour|harbor|port|wharf|pier)\b",
        re.IGNORECASE,
    ),
    "eastern_corridor_doesnt_exist": re.compile(
        r"\b(eastern\s+strip|eastern\s+corridor|sector\s+c)\b",
        re.IGNORECASE,
    ),
}

# Reasons paired with each forbidden pattern
FORBIDDEN_LOCATION_REASONS = {
    "docks_dont_exist": (
        "Astrakov is a sealed inland city — no docks, harbours, or ports exist."
    ),
    "eastern_corridor_doesnt_exist": (
        "Astrakov has no eastern corridor or sector C. "
        "Only the western road toward the Wrocław ruins exists."
    ),
}


# Public functions

def is_neural_id_valid(neural_id):
    """
    Verify that a Neural ID matches the expected format.

    Format: NID-{4 digits}-{1 letter}-{4 alphanum}-{2 alphanum}
    Example valid: NID-7741-X-44A2-9F
    Example invalid: NID-7741-X-44A2 (too short)

    Args:
        neural_id: the string to validate

    Returns:
        bool: True if format is valid
    """
    if not isinstance(neural_id, str):
        raise TypeError(
            f"neural_id must be a string, got {type(neural_id).__name__}"
        )
    return NEURAL_ID_PATTERN.match(neural_id) is not None


def detect_contradictions(answer_text, traveler):
    """
    Scan an interrogation answer for contradictions with the world's facts.

    Uses regex to find mentions of fictional locations or things that
    don't exist in Astrakov.

    Args:
        answer_text: the traveler's spoken answer
        traveler: the Traveler instance (for context-aware checks later)

    Returns:
        list of (pattern_id, reason) tuples — empty if no contradictions
    """
    if not isinstance(answer_text, str):
        raise TypeError(
            f"answer_text must be a string, got {type(answer_text).__name__}"
        )
    if not isinstance(traveler, Traveler):
        raise TypeError(
            f"traveler must be a Traveler instance, got {type(traveler).__name__}"
        )

    contradictions = []

    # Use a comprehension-style scan: for each pattern, see if it matches
    for pattern_id, pattern in FORBIDDEN_LOCATION_PATTERNS.items():
        if pattern.search(answer_text):
            contradictions.append(
                (pattern_id, FORBIDDEN_LOCATION_REASONS[pattern_id])
            )

    return contradictions


def has_documented_contradiction(question):
    """
    Check if this question was authored with a contradiction flag.

    The simpler signal: was the JSON author aware this Q/A reveals a lie?
    Used by the game loop to highlight contradictions in the UI.

    Args:
        question: a Question instance

    Returns:
        bool: True if a contradiction flag is set
    """
    if not isinstance(question, Question):
        raise TypeError(
            f"question must be a Question instance, got {type(question).__name__}"
        )
    return question.has_contradiction()


def is_traveler_lying(traveler, asked_questions):
    """
    Determine if a traveler is lying based on the questions they've answered.

    Combines both signals:
      1. Authored contradiction_flag (the JSON writer's signal)
      2. Regex-detected contradictions in the answer text

    Args:
        traveler: a Traveler instance
        asked_questions: list of Question instances the player has asked

    Returns:
        bool: True if any contradiction was found
    """
    if not isinstance(traveler, Traveler):
        raise TypeError(
            f"traveler must be a Traveler instance, got {type(traveler).__name__}"
        )
    if not isinstance(asked_questions, list):
        raise TypeError(
            f"asked_questions must be a list, got {type(asked_questions).__name__}"
        )

    for question in asked_questions:
        if not isinstance(question, Question):
            raise TypeError(
                f"all asked_questions must be Question instances, "
                f"got {type(question).__name__}"
            )
        # Authored contradiction flag — fastest check
        if question.has_contradiction():
            return True
        # Regex pattern match in the answer text
        if detect_contradictions(question.answer_text, traveler):
            return True

    return False