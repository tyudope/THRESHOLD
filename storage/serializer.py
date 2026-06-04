# storage/serializer.py
"""
Serialization layer converts model objects to dicts (for JSON saving)
and back. Used for save-game files and any future export feature.
"""

from models.traveler import Traveler, Document, Permit
from models.directive import Directive, RuleSet
from models.interrogation import Question
from models.shift import ShiftState, WrongVerdict


# Object → dict (serialize)

def document_to_dict(doc):
    return {
        "name": doc.name,
        "age": doc.age,
        "sector": doc.sector,
        "nationality": doc.nationality,
        "neural_id": doc.neural_id,
        "id_age_years": doc.id_age_years,
    }


def permit_to_dict(permit):
    if permit is None:
        return None
    return {
        "manifest_id": permit.manifest_id,
        "valid_from": permit.valid_from,
        "valid_to": permit.valid_to,
        "sponsor": permit.sponsor,
    }


def question_to_dict(q):
    return {
        "question_text": q.question_text,
        "answer_text": q.answer_text,
        "contradiction_flag": q.contradiction_flag,
        "is_bribe_offer": q.is_bribe_offer,
    }


def traveler_to_dict(traveler):
    questions = getattr(traveler, "questions", [])
    return {
        "name": traveler.document.name,
        "age": traveler.document.age,
        "sector": traveler.document.sector,
        "nationality": traveler.document.nationality,
        "neural_id": traveler.document.neural_id,
        "id_age_years": traveler.document.id_age_years,
        "permit": permit_to_dict(traveler.permit),
        "stated_purpose": traveler.stated_purpose,
        "portrait": list(traveler.portrait),
        "tell": traveler.tell,
        "correct_verdict": traveler.correct_verdict,
        "reason": traveler.reason,
        "is_moral_case": traveler.is_moral_case,
        "has_bribe": traveler.has_bribe,
        "questions": [question_to_dict(q) for q in questions],
    }


def directive_to_dict(d):
    return {
        "number": d.number,
        "text": d.text,
        "rule_id": d.rule_id,
        "is_critical": d.is_critical,
    }


def ruleset_to_dict(rs):
    return {
        "day": rs.day,
        "directives": [directive_to_dict(d) for d in rs.directives],
    }


def wrong_verdict_to_dict(wv):
    return {
        "case_index": wv.case_index,
        "traveler_name": wv.traveler_name,
        "chosen_action": wv.chosen_action,
        "violation": wv.violation,
    }


def shift_state_to_dict(state):
    return {
        "current_traveler_index": state.current_traveler_index,
        "score": state.score,
        "rent": state.rent,
        "consecutive_errors": state.consecutive_errors,
        "total_errors": state.total_errors,
        "time_remaining_seconds": state.time_remaining_seconds,
        "wrong_verdicts": [wrong_verdict_to_dict(w) for w in state.wrong_verdicts],
        "accepted_bribe": state.accepted_bribe,
        "note_read": state.note_read,
    }


# dict → object (deserialize)
def dict_to_document(d):
    return Document(
        name=d["name"],
        age=d["age"],
        sector=d["sector"],
        nationality=d["nationality"],
        neural_id=d["neural_id"],
        id_age_years=d["id_age_years"],
    )


def dict_to_permit(d):
    if d is None:
        return None
    return Permit(
        manifest_id=d["manifest_id"],
        valid_from=d["valid_from"],
        valid_to=d["valid_to"],
        sponsor=d["sponsor"],
    )


def dict_to_question(d):
    return Question(
        question_text=d["question_text"],
        answer_text=d["answer_text"],
        contradiction_flag=d.get("contradiction_flag"),
        is_bribe_offer=d.get("is_bribe_offer", False),
    )


def dict_to_directive(d):
    return Directive(
        number=d["number"],
        text=d["text"],
        rule_id=d["rule_id"],
        is_critical=d.get("is_critical", False),
    )


def dict_to_wrong_verdict(d):
    return WrongVerdict(
        case_index=d["case_index"],
        traveler_name=d["traveler_name"],
        chosen_action=d["chosen_action"],
        violation=d["violation"],
    )


def dict_to_shift_state(d):
    state = ShiftState()
    state.current_traveler_index = d["current_traveler_index"]
    state.score = d["score"]
    state.rent = d["rent"]
    state.consecutive_errors = d["consecutive_errors"]
    state.total_errors = d["total_errors"]
    state.time_remaining_seconds = d["time_remaining_seconds"]
    state.wrong_verdicts = [dict_to_wrong_verdict(w) for w in d["wrong_verdicts"]]
    state.accepted_bribe = d["accepted_bribe"]
    state.note_read = d["note_read"]
    return state