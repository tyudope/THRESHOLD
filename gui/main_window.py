# gui/main_window.py
"""
GameWindow - the tkinter front end for THRESHOLD.

This is the GUI sibling of cli/menu.py. It drives the exact same flow
(title → directives → five travelers with the note before #2 → end of
shift → arrest if triggered) over the same domain objects, but renders
into tk widgets and advances via root.after() instead of input()/sleep().

The ShiftClock runs on its own background thread; we only ever read it
(time_remaining / is_expired / raise_if_expired) from the after()-driven
tick callback on the main thread, never the reverse.
"""

import tkinter as tk

from cli.decorators import log_action
from core.catalog import Catalog
from core.clock import ShiftClock
from core.internal_affairs import ENDING_ARRESTED
from core.lie_detector import detect_contradictions
from core.verdict import compute_shift_result
from exceptions import ReviewTriggeredError, ShiftExpiredError, ThresholdError
from models.interrogation import InterrogationSession
from models.shift import (
    ShiftState,
    TIME_COST_PER_NOTE_READ,
    TIME_COST_PER_QUESTION,
    TOTAL_TRAVELERS,
)

from gui import theme_tk as t
from gui.widgets import (
    ArrestWindow,
    DirectivesPanel,
    EndingWindow,
    FeedbackBanner,
    InterrogationDialog,
    NoteDialog,
    StatsBar,
    TravelerCard,
)

WIDTH = 920
HEIGHT = 720
FEEDBACK_PAUSE_MS = 8000


class GameWindow(tk.Tk):
    """Top-level application window owning the whole shift."""

    def __init__(self):
        super().__init__()
        self.title("THRESHOLD")
        self.geometry(f"{WIDTH}x{HEIGHT}")
        self.configure(bg=t.BG_DARK)

        # Domain objects - created when the shift actually starts.
        self.catalog = None
        self.state = None
        self.clock = None

        # Flow bookkeeping.
        self.case_number = 0
        self.traveler = None
        self.review_triggered = False
        self.case_resolved = False
        self._ended = False
        self._clock_job = None
        self._modal = None

        # UI handles built in _build_game_ui.
        self.statsbar = None
        self.directives_panel = None
        self.center = None
        self.feedback = None
        self.action_buttons = {}

        self._build_title()

    # Title screen

    def _build_title(self):
        self._title_frame = tk.Frame(self, bg=t.BG_DARK)
        self._title_frame.pack(fill="both", expand=True)

        tk.Label(
            self._title_frame, text="THRESHOLD", bg=t.BG_DARK, fg=t.FG_RUST,
            font=("Courier New", 56, "bold"),
        ).pack(pady=(170, 6))
        tk.Label(
            self._title_frame, text="NEW ASTRAKOV CUSTOMS · GATE 9",
            bg=t.BG_DARK, fg=t.FG_TEAL, font=t.FONT_SUBHEADER,
        ).pack()
        tk.Label(
            self._title_frame,
            text="The State watches itself through eyes like yours.",
            bg=t.BG_DARK, fg=t.FG_GRAY, font=t.FONT_MONO,
        ).pack(pady=(10, 30))

        begin = tk.Button(
            self._title_frame, text="Press any button to begin",
            command=self._start_game,
        )
        t.style_button(begin, fg=t.FG_GREEN)
        begin.pack()

        # Any key or click anywhere also starts the shift.
        self.bind("<Key>", self._title_key)
        self.bind("<Button-1>", self._title_key)

    def _title_key(self, _event=None):
        if self._title_frame.winfo_exists():
            self._start_game()

    # Start of shift

    @log_action
    def _start_game(self):
        self.unbind("<Key>")
        self.unbind("<Button-1>")
        if self._title_frame.winfo_exists():
            self._title_frame.destroy()

        try:
            self.catalog = Catalog.load_default()
        except ThresholdError as exc:
            self._fatal(f"Could not load game content: {exc}")
            return

        self.state = ShiftState()
        self.clock = ShiftClock()

        self._build_game_ui()
        self.clock.start()
        self._tick()

        self.case_number = 1
        self._present_traveler()

    def _build_game_ui(self):
        self.statsbar = StatsBar(self)
        self.statsbar.pack(side="top", fill="x")

        self.directives_panel = DirectivesPanel(self, self.catalog.ruleset)
        self.directives_panel.pack(side="top", fill="x")

        action_frame = tk.Frame(self, bg=t.BG_PANEL, bd=1, relief="ridge")
        action_frame.pack(side="bottom", fill="x")
        self._build_actions(action_frame)

        self.feedback = FeedbackBanner(self)
        self.feedback.pack(side="bottom", fill="x", pady=6)

        self.center = tk.Frame(self, bg=t.BG_DARK)
        self.center.pack(side="top", fill="both", expand=True, padx=20, pady=10)

    def _build_actions(self, parent):
        specs = [
            ("I", "INTERROGATE (-15s)", t.FG_PURPLE, self._on_interrogate),
            ("A", "APPROVE", t.FG_GREEN, lambda: self._on_verdict("approve")),
            ("D", "DENY", t.FG_YELLOW, lambda: self._on_verdict("deny")),
            ("X", "DETAIN", t.FG_RED, lambda: self._on_verdict("detain")),
        ]
        for col, (key, label, color, command) in enumerate(specs):
            btn = tk.Button(parent, text=f"[{key}] {label}", command=command)
            t.style_button(btn, fg=color)
            btn.grid(row=0, column=col, sticky="ew", padx=6, pady=8)
            parent.grid_columnconfigure(col, weight=1)
            self.action_buttons[key] = btn

    def _set_actions(self, enabled):
        state = "normal" if enabled else "disabled"
        for btn in self.action_buttons.values():
            btn.config(state=state)

    # Clock tick (once per second on the main thread)

    def _tick(self):
        if self._ended:
            return
        try:
            self.statsbar.update(self.state, self.clock)
            self.clock.raise_if_expired()
        except ShiftExpiredError:
            self._on_expiry()
            return
        self._clock_job = self.after(1000, self._tick)

    def _on_expiry(self):
        if self._modal is not None and self._modal.winfo_exists():
            self._modal.destroy()
            self._modal = None
        self._end_shift(review_triggered=False)

    # Per-traveler presentation

    def _present_traveler(self):
        """Show the current traveler - with the note interstitial before #2."""
        if self.case_number == 2 and not self.state.note_read:
            self._modal = NoteDialog(self, self.catalog.dialogue, self._on_note_choice)
        else:
            self._show_current_card()

    def _on_note_choice(self, choice):
        if choice == "R":
            self.state.mark_note_read()
            self.clock.consume(TIME_COST_PER_NOTE_READ)
        # The card is shown once the dialog closes; schedule it so the
        # "Continue" view of the note has a beat to be read first.
        self.after(50, self._show_current_card)

    def _show_current_card(self):
        if self._ended:
            return
        self.traveler = self.catalog.travelers[self.case_number - 1]
        self.case_resolved = False
        self.feedback.clear()

        for child in self.center.winfo_children():
            child.destroy()
        card = TravelerCard(
            self.center, self.traveler, self.case_number, TOTAL_TRAVELERS
        )
        card.pack(anchor="nw")
        self._set_actions(True)

    # Actions

    def _on_interrogate(self):
        if self.case_resolved:
            return
        if self.state.current_interrogation is None:
            self.state.current_interrogation = InterrogationSession(
                self.traveler.questions,
                max_questions=2,
                time_cost_per_question=TIME_COST_PER_QUESTION,
            )
        self._modal = InterrogationDialog(
            self,
            self.traveler,
            self.state.current_interrogation,
            on_pick=self._on_interrogation_pick,
            on_bribe_accept=self._on_bribe_accept,
            on_close=self._on_interrogation_close,
        )

    def _on_interrogation_pick(self, index):
        """Domain side of asking a question; returns (question, contradiction)."""
        try:
            question = self.state.current_interrogation.ask(index)
        except ThresholdError:
            return None
        self.state.consume_time(TIME_COST_PER_QUESTION)
        self.clock.consume(TIME_COST_PER_QUESTION)

        contradictions = detect_contradictions(question.answer_text, self.traveler)
        contradiction_text = contradictions[0][1] if contradictions else None
        return question, contradiction_text

    def _on_interrogation_close(self):
        self._modal = None

    def _on_bribe_accept(self):
        self._modal = None
        self.state.record_bribe()
        self.feedback.bribe()
        self.case_resolved = True
        self._set_actions(False)
        self.after(FEEDBACK_PAUSE_MS, self._after_verdict)

    def _on_verdict(self, action):
        if self.case_resolved:
            return
        self.case_resolved = True
        self._set_actions(False)
        self._resolve_verdict(action)
        self.after(FEEDBACK_PAUSE_MS, self._after_verdict)

    def _resolve_verdict(self, action):
        """Mirror of cli/menu.py's _resolve_verdict, rendered as a banner."""
        name = self.traveler.document.name

        if (
            action == "approve"
            and self.traveler.is_moral_case
            and self.traveler.correct_verdict == "deny"
        ):
            self.state.record_moral_violation(
                self.case_number,
                name,
                "Approved a Hawkmoor resident in violation of Directive 03.",
            )
            self.feedback.moral(self.traveler.reason)
        elif action == self.traveler.correct_verdict:
            self.state.record_correct()
            self.feedback.correct(self.traveler.reason)
        else:
            violation = self.traveler.reason.split(".")[0] + "."
            self.state.record_wrong(self.case_number, name, action, violation)
            rent_change = -2 if action == "detain" else -1
            self.feedback.incorrect(self.traveler.reason, rent_change, action)

    def _after_verdict(self):
        """Advance the traveler; route to arrest if the review threshold is hit."""
        if self._ended:
            return
        try:
            self.state.advance_traveler()
            if self.state.should_trigger_review():
                raise ReviewTriggeredError("Internal Affairs has flagged the booth.")
        except ReviewTriggeredError:
            self._end_shift(review_triggered=True)
            return
        self._next_case()

    def _next_case(self):
        self.case_number += 1
        if self.case_number > TOTAL_TRAVELERS:
            self._end_shift(review_triggered=False)
        else:
            self._present_traveler()

    # End of shift

    def _end_shift(self, review_triggered):
        if self._ended:
            return
        self._ended = True
        self.review_triggered = review_triggered

        if self._clock_job is not None:
            self.after_cancel(self._clock_job)
            self._clock_job = None
        self.clock.stop()
        self._set_actions(False)

        result = compute_shift_result(self.state, review_triggered=review_triggered)

        if result.ending_key == ENDING_ARRESTED:
            self._modal = ArrestWindow(
                self, self.state, self.catalog.dialogue,
                on_accept=lambda: self._show_ending(result),
            )
        else:
            self._show_ending(result)

    def _show_ending(self, result):
        self._modal = EndingWindow(
            self, result, self.catalog.dialogue, on_exit=self._quit
        )

    def _quit(self):
        self.destroy()

    # Errors

    def _fatal(self, message):
        """Replace the window contents with a clean error message."""
        for child in self.winfo_children():
            child.destroy()
        tk.Label(
            self, text="ERROR", bg=t.BG_DARK, fg=t.FG_RED, font=t.FONT_HEADER,
        ).pack(pady=(120, 10))
        tk.Label(
            self, text=message, bg=t.BG_DARK, fg=t.FG_RED, font=t.FONT_MONO,
            wraplength=700, justify="center",
        ).pack(padx=20)
        quit_btn = tk.Button(self, text="Exit", command=self.destroy)
        t.style_button(quit_btn, fg=t.FG_GRAY)
        quit_btn.pack(pady=30)
