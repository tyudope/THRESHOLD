# models/interrogation.py
"""
Interrogation data model one traveler's possible Q&A pairs and the
per-case session state that tracks what the player has asked.

Each Traveler has a list of Question objects loaded with them. When the
traveler arrives at the booth, an InterrogationSession is created to
track which questions the player has used and how much time is left in
the per-case budget.
"""

from exceptions import InvalidQuestionError


class Question:
    """One Q&A pair the player can choose during interrogation."""

    def __init__(self, question_text, answer_text, contradiction_flag=None, is_bribe_offer=False):
        # question_text
        if not isinstance(question_text, str) or not question_text.strip():
            raise InvalidQuestionError("question_text must be a non-empty string")

        # answer_text
        if not isinstance(answer_text, str) or not answer_text.strip():
            raise InvalidQuestionError("answer_text must be a non-empty string")

        # contradiction_flag (optional)
        if contradiction_flag is not None and not isinstance(contradiction_flag, str):
            raise InvalidQuestionError(
                f"contradiction_flag must be a string or None, "
                f"got {type(contradiction_flag).__name__}"
            )

        # is_bribe_offer
        if not isinstance(is_bribe_offer, bool):
            raise InvalidQuestionError("is_bribe_offer must be a bool")

        self.question_text = question_text.strip()
        self.answer_text = answer_text.strip()
        self.contradiction_flag = contradiction_flag.strip() if contradiction_flag else None
        self.is_bribe_offer = is_bribe_offer

    def has_contradiction(self):
        """Return True if this answer contradicts the traveler's documents."""
        return self.contradiction_flag is not None

    def __repr__(self):
        return f"Question(text='{self.question_text[:30]}...')"


class InterrogationSession:
    """tracks asked questions and remaining budget."""

    def __init__(self, available_questions, max_questions=2, time_cost_per_question=15):
        # available_questions
        if not isinstance(available_questions, list):
            raise InvalidQuestionError(
                f"available_questions must be a list, "
                f"got {type(available_questions).__name__}"
            )
        if not available_questions:
            raise InvalidQuestionError("available_questions cannot be empty")
        for q in available_questions:
            if not isinstance(q, Question):
                raise InvalidQuestionError(
                    f"all available_questions must be Question instances, "
                    f"got {type(q).__name__}"
                )

        # max_questions
        if not isinstance(max_questions, int) or isinstance(max_questions, bool):
            raise InvalidQuestionError("max_questions must be an int")
        if max_questions < 1:
            raise InvalidQuestionError("max_questions must be at least 1")

        # time_cost_per_question
        if not isinstance(time_cost_per_question, int) or isinstance(time_cost_per_question, bool):
            raise InvalidQuestionError("time_cost_per_question must be an int")
        if time_cost_per_question < 0:
            raise InvalidQuestionError("time_cost_per_question cannot be negative")

        self.available_questions = list(available_questions)    # defensive copy
        self.asked_indices = set()
        self.max_questions = max_questions
        self.time_cost_per_question = time_cost_per_question

    def can_ask_more(self):
        """Return True if the player has questions remaining in budget."""
        return len(self.asked_indices) < self.max_questions

    def ask(self, index):
        """Mark a question as asked and return it. Raises if already asked or out of budget."""
        if not isinstance(index, int) or isinstance(index, bool):
            raise InvalidQuestionError(
                f"index must be an int, got {type(index).__name__}"
            )
        if index < 0 or index >= len(self.available_questions):
            raise InvalidQuestionError(
                f"index {index} out of range (0–{len(self.available_questions) - 1})"
            )
        if index in self.asked_indices:
            raise InvalidQuestionError(f"question {index} has already been asked")
        if not self.can_ask_more():
            raise InvalidQuestionError(
                f"question budget exhausted ({self.max_questions} max)"
            )

        self.asked_indices.add(index)
        return self.available_questions[index]

    def remaining_questions(self):
        """Return how many questions the player can still ask."""
        return self.max_questions - len(self.asked_indices)

    def __repr__(self):
        return (
            f"InterrogationSession("
            f"asked={len(self.asked_indices)}/{self.max_questions}, "
            f"available={len(self.available_questions)})"
        )