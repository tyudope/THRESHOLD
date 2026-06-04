# core/catalog.py
"""
Content loader for THRESHOLD.

Reads JSON files from data/, converts raw dicts into model objects, and
exposes them through a single Catalog instance. Game code consumes the
Catalog and never touches JSON directly.

The catalog is the hydration boundary: untyped JSON enters here, typed
domain objects exit here.
"""

import json
from pathlib import Path

from exceptions import CorruptedDataError
from models.traveler import Traveler, Document, Permit
from models.directive import Directive, RuleSet
from models.interrogation import Question


# Default data file locations (relative to project root)
DATA_DIR = Path("data")
TRAVELERS_FILE = DATA_DIR / "travelers.json"
DIRECTIVES_FILE = DATA_DIR / "directives.json"
DIALOGUE_FILE = DATA_DIR / "inspector_dialogue.json"

# Private loaders — each reads one file and returns domain objects

def _read_json(path):
    """Read and parse a JSON file. Raises CorruptedDataError on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise CorruptedDataError(f"Data file not found: {path}")
    except json.JSONDecodeError as e:
        raise CorruptedDataError(f"Invalid JSON in {path}: {e}")


def _build_question(question_dict):
    """Convert one question dict from JSON into a Question object."""
    return Question(
        question_text=question_dict["question_text"],
        answer_text=question_dict["answer_text"],
        contradiction_flag=question_dict.get("contradiction_flag"),
        is_bribe_offer=question_dict.get("is_bribe_offer", False),
    )


def _build_permit(permit_dict):
    """Convert one permit dict (or None) from JSON into a Permit or None."""
    if permit_dict is None:
        return None
    return Permit(
        manifest_id=permit_dict["manifest_id"],
        valid_from=permit_dict["valid_from"],
        valid_to=permit_dict["valid_to"],
        sponsor=permit_dict["sponsor"],
    )


def _build_traveler(traveler_dict):
    """Convert one traveler dict from JSON into a Traveler object."""
    document = Document(
        name=traveler_dict["name"],
        age=traveler_dict["age"],
        sector=traveler_dict["sector"],
        nationality=traveler_dict["nationality"],
        neural_id=traveler_dict["neural_id"],
        id_age_years=traveler_dict["id_age_years"],
    )
    permit = _build_permit(traveler_dict.get("permit"))
    questions = [_build_question(q) for q in traveler_dict.get("questions", [])]

    traveler = Traveler(
        document=document,
        stated_purpose=traveler_dict["stated_purpose"],
        portrait=traveler_dict["portrait"],
        correct_verdict=traveler_dict["correct_verdict"],
        reason=traveler_dict["reason"],
        permit=permit,
        tell=traveler_dict.get("tell"),
        is_moral_case=traveler_dict.get("is_moral_case", False),
        has_bribe=traveler_dict.get("has_bribe", False),
    )
    # Stash questions on the traveler as an attribute (not a field on the class)
    # so the game loop can build InterrogationSession instances later.
    traveler.questions = questions
    return traveler


def _load_travelers(path=TRAVELERS_FILE):
    """Read travelers.json and return a list of Traveler objects."""
    data = _read_json(path)
    if "travelers" not in data or not isinstance(data["travelers"], list):
        raise CorruptedDataError(
            f"{path} is missing the 'travelers' list at the top level."
        )
    return [_build_traveler(t) for t in data["travelers"]]


def _build_directive(directive_dict):
    """Convert one directive dict from JSON into a Directive object."""
    return Directive(
        number=directive_dict["number"],
        text=directive_dict["text"],
        rule_id=directive_dict["rule_id"],
        is_critical=directive_dict.get("is_critical", False),
    )


def _load_ruleset(path=DIRECTIVES_FILE):
    """Read directives.json and return a RuleSet object."""
    data = _read_json(path)
    if "directives" not in data or not isinstance(data["directives"], list):
        raise CorruptedDataError(
            f"{path} is missing the 'directives' list at the top level."
        )
    if "day" not in data:
        raise CorruptedDataError(f"{path} is missing the 'day' field.")

    directives = [_build_directive(d) for d in data["directives"]]
    return RuleSet(day=data["day"], directives=directives)


def _load_dialogue(path=DIALOGUE_FILE):
    """Read inspector_dialogue.json and return the raw dict (used as-is)."""
    return _read_json(path)


# Catalog — the public interface

class Catalog:
    """The loaded content of THRESHOLD — travelers, ruleset, dialogue."""

    def __init__(self, travelers, ruleset, dialogue):
        self.travelers = list(travelers)        # defensive copy
        self.ruleset = ruleset
        self.dialogue = dialogue

    @classmethod
    def load_default(cls):
        """Load all three files from their default locations."""
        return cls(
            travelers=_load_travelers(),
            ruleset=_load_ruleset(),
            dialogue=_load_dialogue(),
        )

    @classmethod
    def load_from(cls, travelers_path, directives_path, dialogue_path):
        """Load from specified paths — useful for tests."""
        return cls(
            travelers=_load_travelers(travelers_path),
            ruleset=_load_ruleset(directives_path),
            dialogue=_load_dialogue(dialogue_path),
        )

    def traveler_count(self):
        """Return how many travelers are in this catalog."""
        return len(self.travelers)

    def __repr__(self):
        return (
            f"Catalog(travelers={len(self.travelers)}, "
            f"directives={len(self.ruleset.directives)}, "
            f"day={self.ruleset.day})"
        )