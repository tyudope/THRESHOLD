# models/directive.py
"""
Directive and RuleSet models — the State's rules at the start of a shift.

Each Directive is a single rule with both human-readable text (shown to
the player) and a machine identifier (used by the validator). A RuleSet
groups all directives for one shift.

This file is pure data — validation logic lives in core/validator.py.
"""

from exceptions import InvalidDirectiveError


class Directive:
    """A single rule from the State for the current shift."""

    def __init__(self, number, text, rule_id, is_critical=False):
        # number
        if not isinstance(number, int) or isinstance(number, bool):
            raise InvalidDirectiveError(
                f"number must be an int, got {type(number).__name__}"
            )
        if number < 1:
            raise InvalidDirectiveError("number must be at least 1")

        # text
        if not isinstance(text, str) or not text.strip():
            raise InvalidDirectiveError("text must be a non-empty string")

        # rule_id
        if not isinstance(rule_id, str) or not rule_id.strip():
            raise InvalidDirectiveError("rule_id must be a non-empty string")

        # is_critical 
        if not isinstance(is_critical, bool):
            raise InvalidDirectiveError("is_critical must be a bool")

        self.number = number
        self.text = text.strip()
        self.rule_id = rule_id.strip()
        self.is_critical = is_critical

    def __repr__(self):
        return f"Directive(number={self.number}, rule_id='{self.rule_id}')"


class RuleSet:
    """All directives in force during one shift."""

    def __init__(self, day, directives):
        # --- day ---
        if not isinstance(day, int) or isinstance(day, bool):
            raise InvalidDirectiveError(
                f"day must be an int, got {type(day).__name__}"
            )
        if day < 1:
            raise InvalidDirectiveError("day must be at least 1")

        # --- directives ---
        if not isinstance(directives, list):
            raise InvalidDirectiveError(
                f"directives must be a list, got {type(directives).__name__}"
            )
        if not directives:
            raise InvalidDirectiveError("directives cannot be empty")
        for d in directives:
            if not isinstance(d, Directive):
                raise InvalidDirectiveError(
                    f"all directives must be Directive instances, got {type(d).__name__}"
                )

        # check rule_ids are unique (no duplicate rules in one set)
        rule_ids = [d.rule_id for d in directives]
        if len(rule_ids) != len(set(rule_ids)):
            raise InvalidDirectiveError("directives contain duplicate rule_ids")

        self.day = day
        self.directives = list(directives)        # defensive copy

    def get_by_id(self, rule_id):
        """Find a directive by its machine ID. Returns None if not found."""
        for d in self.directives:
            if d.rule_id == rule_id:
                return d
        return None

    def __repr__(self):
        return f"RuleSet(day={self.day}, directives={len(self.directives)})"