# models/traveler.py
"""
Traveler data model represents one person attempting to cross the border.

Each Traveler composes a Document (identity papers) and an optional Permit
(travel manifest). Construction is the only validation boundary once a
Traveler exists, downstream code can trust the data.
"""

from exceptions import InvalidTravelerError


VALID_VERDICTS = {"approve", "deny", "detain"}


class Document:
    """Neural ID Chip carried by every traveler."""

    def __init__(self, name, age, sector, nationality, neural_id, id_age_years):
        # --- name ---
        if not isinstance(name, str):
            raise InvalidTravelerError(
                f"name must be a string, got {type(name).__name__}"
            )
        name = name.strip()
        if not name:
            raise InvalidTravelerError("name cannot be empty")

        # --- age ---
        if not isinstance(age, int) or isinstance(age, bool):
            raise InvalidTravelerError(
                f"age must be an int, got {type(age).__name__}"
            )
        if age < 0:
            raise InvalidTravelerError("age cannot be negative")

        # --- sector ---
        if not isinstance(sector, str) or not sector.strip():
            raise InvalidTravelerError("sector must be a non-empty string")

        # --- nationality ---
        if not isinstance(nationality, str) or not nationality.strip():
            raise InvalidTravelerError("nationality must be a non-empty string")

        # --- neural_id ---
        if not isinstance(neural_id, str) or not neural_id.strip():
            raise InvalidTravelerError("neural_id must be a non-empty string")

        # --- id_age_years ---
        if not isinstance(id_age_years, int) or isinstance(id_age_years, bool):
            raise InvalidTravelerError(
                f"id_age_years must be an int, got {type(id_age_years).__name__}"
            )
        if id_age_years < 0:
            raise InvalidTravelerError("id_age_years cannot be negative")

        self.name = name
        self.age = age
        self.sector = sector.strip()
        self.nationality = nationality.strip()
        self.neural_id = neural_id.strip()
        self.id_age_years = id_age_years

    def __repr__(self):
        return (
            f"Document(name='{self.name}', nationality='{self.nationality}', "
            f"neural_id='{self.neural_id}')"
        )


class Permit:
    """Travel manifest - required for non-Astrakov citizens."""

    def __init__(self, manifest_id, valid_from, valid_to, sponsor):
        if not isinstance(manifest_id, str) or not manifest_id.strip():
            raise InvalidTravelerError("manifest_id must be a non-empty string")
        if not isinstance(valid_from, str) or not valid_from.strip():
            raise InvalidTravelerError("valid_from must be a non-empty string")
        if not isinstance(valid_to, str) or not valid_to.strip():
            raise InvalidTravelerError("valid_to must be a non-empty string")
        if not isinstance(sponsor, str):
            raise InvalidTravelerError(
                f"sponsor must be a string, got {type(sponsor).__name__}"
            )

        self.manifest_id = manifest_id.strip()
        self.valid_from = valid_from.strip()
        self.valid_to = valid_to.strip()
        self.sponsor = sponsor.strip()

    def __repr__(self):
        return f"Permit(manifest_id='{self.manifest_id}', sponsor='{self.sponsor}')"


class Traveler:
    """One person at Gate 9 - composes Document, optional Permit, and game metadata."""

    def __init__(
        self,
        document,
        stated_purpose,
        portrait,
        correct_verdict,
        reason,
        permit=None,
        tell=None,
        is_moral_case=False,
        has_bribe=False,
    ):
        # --- document ---
        if not isinstance(document, Document):
            raise InvalidTravelerError(
                f"document must be a Document instance, got {type(document).__name__}"
            )

        # --- permit (optional) ---
        if permit is not None and not isinstance(permit, Permit):
            raise InvalidTravelerError(
                f"permit must be a Permit instance or None, got {type(permit).__name__}"
            )

        # --- stated_purpose ---
        if not isinstance(stated_purpose, str) or not stated_purpose.strip():
            raise InvalidTravelerError("stated_purpose must be a non-empty string")

        # --- portrait ---
        if not isinstance(portrait, list):
            raise InvalidTravelerError(
                f"portrait must be a list of strings, got {type(portrait).__name__}"
            )
        if not portrait:
            raise InvalidTravelerError("portrait cannot be empty")
        for line in portrait:
            if not isinstance(line, str):
                raise InvalidTravelerError(
                    f"all portrait lines must be strings, got {type(line).__name__}"
                )

        # --- correct_verdict ---
        if correct_verdict not in VALID_VERDICTS:
            raise InvalidTravelerError(
                f"correct_verdict must be one of {VALID_VERDICTS}, got '{correct_verdict}'"
            )

        # --- reason ---
        if not isinstance(reason, str) or not reason.strip():
            raise InvalidTravelerError("reason must be a non-empty string")

        # --- tell (optional) ---
        if tell is not None and not isinstance(tell, str):
            raise InvalidTravelerError(
                f"tell must be a string or None, got {type(tell).__name__}"
            )

        # --- is_moral_case ---
        if not isinstance(is_moral_case, bool):
            raise InvalidTravelerError("is_moral_case must be a bool")

        # --- has_bribe ---
        if not isinstance(has_bribe, bool):
            raise InvalidTravelerError("has_bribe must be a bool")

        self.document = document
        self.permit = permit
        self.stated_purpose = stated_purpose.strip()
        self.portrait = list(portrait)        # defensive copy
        self.correct_verdict = correct_verdict
        self.reason = reason.strip()
        self.tell = tell.strip() if tell else None
        self.is_moral_case = is_moral_case
        self.has_bribe = has_bribe

    def __repr__(self):
        return (
            f"Traveler(name='{self.document.name}', "
            f"nationality='{self.document.nationality}', "
            f"correct_verdict='{self.correct_verdict}')"
        )