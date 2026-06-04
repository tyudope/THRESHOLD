# core/validator.py
"""
Rules engine — validates a Traveler against a RuleSet of Directives.

Pure functions, no side effects. Each rule has its own function for clarity
and testability. The orchestrator `validate_traveler` runs them in order and
short-circuits at the first violation.

The validator only handles document-based verdicts (approve/deny). Detection
of lies (which triggers a 'detain' verdict) lives in core/lie_detector.py
because it requires interrogation evidence, not document data.
"""

from models.traveler import Traveler
from models.directive import RuleSet

# Result container


class ValidationResult:
    """The output of running the validator: verdict + human-readable reason."""

    def __init__(self, verdict, reason):
        if verdict not in {"approve", "deny"}:
            raise ValueError(
                f"verdict must be 'approve' or 'deny', got '{verdict}'"
            )
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason must be a non-empty string")

        self.verdict = verdict
        self.reason = reason.strip()

    def __repr__(self):
        short_reason = (
            self.reason if len(self.reason) <= 50 else self.reason[:50] + "..."
        )
        return f"ValidationResult(verdict='{self.verdict}', reason='{short_reason}')"


# Individual rule functions
# Contract: each takes a Traveler and returns (is_violated: bool, reason: str)


def check_neural_id_valid(traveler):
    """Directive 01: Neural ID must be issued under 5 years ago."""
    if traveler.document.id_age_years > 5:
        return (True, f"Neural ID is {traveler.document.id_age_years} years old (Directive 01 requires under 5).")
    return (False, "")


def check_manifest_required(traveler):
    """Directive 02: outsiders need a manifest; Astrakov citizens do not."""
    if traveler.document.nationality != "Astrakov" and traveler.permit is None:
        return (True, f"Traveler from {traveler.document.nationality} sector has no manifest (Directive 02 requires one for non-Astrakov citizens).")
    return (False, "")


def check_hawkmoor_ban(traveler):
    """Directive 03: Hawkmoor nationals are banned regardless of papers."""
    if traveler.document.nationality == "Hawkmoor":
        return (True, "Hawkmoor resident — Directive 03 bans all Hawkmoor citizens regardless of papers or sponsorship.")
    return (False, "")


def check_minor_has_sponsor(traveler):
    """Directive 04: minors (under 18) must have a sponsor on the manifest."""
    if traveler.document.age >= 18:
        return (False, "")

    if traveler.permit is None:
        return (True, f"Minor (age {traveler.document.age}) has no manifest (Directive 04 requires a sponsor).")

    if traveler.permit.sponsor.upper() == "UNLISTED" or not traveler.permit.sponsor:
        return (True, f"Minor (age {traveler.document.age}) has no sponsor listed on manifest (Directive 04).")

    return (False, "")


# Rule lookup — maps rule_id (from JSON) to checker function

RULE_CHECKERS = {
    "valid_neural_id":                check_neural_id_valid,
    "manifest_required_for_outsiders": check_manifest_required,
    "hawkmoor_banned":                check_hawkmoor_ban,
    "minor_needs_sponsor":            check_minor_has_sponsor,
}


# Orchestrator


def validate_traveler(traveler, ruleset):
    """
    Apply every directive in ruleset against the traveler.

    Returns ValidationResult with verdict='approve' if no violations,
    or verdict='deny' with the first violation's reason.
    """
    if not isinstance(traveler, Traveler):
        raise TypeError(
            f"traveler must be a Traveler instance, got {type(traveler).__name__}"
        )
    if not isinstance(ruleset, RuleSet):
        raise TypeError(
            f"ruleset must be a RuleSet instance, got {type(ruleset).__name__}"
        )

    for directive in ruleset.directives:
        if directive.rule_id not in RULE_CHECKERS:
            raise ValueError(
                f"No checker registered for rule_id '{directive.rule_id}'. "
                f"Add it to RULE_CHECKERS in core/validator.py."
            )

        is_violated, reason = RULE_CHECKERS[directive.rule_id](traveler)
        if is_violated:
            return ValidationResult(
                verdict="deny",
                reason=f"Directive {directive.number} violated. {reason}",
            )

    return ValidationResult(
        verdict="approve",
        reason="All directives satisfied. Documents are in order.",
    )


# Helper: list ALL violations (not just the first)


def list_all_violations(traveler, ruleset):
    """Return a list of (directive_number, reason) tuples for every violation."""
    if not isinstance(traveler, Traveler):
        raise TypeError(
            f"traveler must be a Traveler instance, got {type(traveler).__name__}"
        )
    if not isinstance(ruleset, RuleSet):
        raise TypeError(
            f"ruleset must be a RuleSet instance, got {type(ruleset).__name__}"
        )

    violations = []
    for directive in ruleset.directives:
        if directive.rule_id not in RULE_CHECKERS:
            raise ValueError(
                f"No checker registered for rule_id '{directive.rule_id}'. "
                f"Add it to RULE_CHECKERS in core/validator.py."
            )

        is_violated, reason = RULE_CHECKERS[directive.rule_id](traveler)
        if is_violated:
            violations.append((directive.number, reason))

    return violations