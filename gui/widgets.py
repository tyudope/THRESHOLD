# gui/widgets.py
"""
Reusable tkinter widgets for THRESHOLD's GUI.

Every widget here is pure presentation: it takes domain objects (Traveler,
RuleSet, ShiftState, ShiftResult, the dialogue dict) and draws them. None of
these widgets decide game rules — they call into core/ only to format what
the CLI already formats (contradictions, the arrest speech). Flow control
lives in gui/main_window.py.

Convention: pack() at the top level of each Toplevel, grid() inside frames.
"""

import tkinter as tk

from gui import theme_tk as t
from core.internal_affairs import generate_review_speech


# Directives panel

class DirectivesPanel(tk.Frame):
    """A strip listing the day's directives; critical ones in red."""

    def __init__(self, parent, ruleset):
        super().__init__(parent, bg=t.BG_PANEL, bd=1, relief="ridge")
        title = tk.Label(
            self,
            text=f"DIRECTIVE FOR TODAY — Day {ruleset.day}",
            bg=t.BG_PANEL,
            fg=t.FG_RUST,
            font=t.FONT_SUBHEADER,
            anchor="w",
        )
        title.pack(fill="x", padx=10, pady=(6, 2))

        for directive in ruleset.directives:
            color = t.FG_RED if directive.is_critical else t.FG_TEXT
            row = tk.Label(
                self,
                text=f"  {directive.number:02d}.  {directive.text}",
                bg=t.BG_PANEL,
                fg=color,
                font=t.FONT_MONO,
                anchor="w",
                justify="left",
            )
            row.pack(fill="x", padx=10)
        tk.Frame(self, bg=t.BG_PANEL, height=4).pack()


# Traveler card

class TravelerCard(tk.Frame):
    """Portrait (left, monospace) + document fields (right)."""

    def __init__(self, parent, traveler, case_number, total):
        super().__init__(parent, bg=t.BG_DARK)
        doc = traveler.document

        header = tk.Label(
            self,
            text=f"TRAVELER {case_number} OF {total}",
            bg=t.BG_DARK,
            fg=t.FG_TEAL,
            font=t.FONT_SUBHEADER,
        )
        header.grid(row=0, column=0, columnspan=2, sticky="w", pady=(4, 8))

        # Left column — ASCII portrait
        portrait = tk.Label(
            self,
            text="\n".join(traveler.portrait),
            bg=t.BG_DARK,
            fg=t.FG_RUST,
            font=t.FONT_MONO,
            justify="left",
            anchor="nw",
        )
        portrait.grid(row=1, column=0, sticky="nw", padx=(0, 24))

        # Right column — identity + manifest + purpose
        info = tk.Frame(self, bg=t.BG_DARK)
        info.grid(row=1, column=1, sticky="nw")

        self._section(info, "── IDENTITY ──")
        self._field(info, "Name", doc.name)
        self._field(info, "Age", str(doc.age))
        self._field(info, "Sector", doc.sector)
        self._field(info, "Nation", doc.nationality)
        self._field(info, "NID", doc.neural_id)
        self._field(info, "Status", f"ID issued {doc.id_age_years}y ago")

        self._section(info, "── TRAVEL MANIFEST ──")
        if traveler.permit is not None:
            p = traveler.permit
            self._field(info, "Manifest", p.manifest_id)
            self._field(info, "Valid", f"{p.valid_from} → {p.valid_to}")
            self._field(info, "Sponsor", p.sponsor)
        else:
            tk.Label(
                info, text="(none submitted)", bg=t.BG_DARK, fg=t.FG_RED,
                font=t.FONT_MONO, anchor="w",
            ).pack(fill="x")

        self._section(info, "── STATED PURPOSE ──")
        tk.Label(
            info, text=traveler.stated_purpose, bg=t.BG_DARK, fg=t.FG_GRAY,
            font=t.FONT_MONO, anchor="w", justify="left", wraplength=460,
        ).pack(fill="x")

        if traveler.tell:
            tk.Label(
                info, text=f"* {traveler.tell}", bg=t.BG_DARK, fg=t.FG_GRAY,
                font=t.FONT_MONO_SMALL, anchor="w", justify="left", wraplength=460,
            ).pack(fill="x", pady=(8, 0))

    def _section(self, parent, text):
        tk.Label(
            parent, text=text, bg=t.BG_DARK, fg=t.FG_GRAY,
            font=t.FONT_LABEL, anchor="w",
        ).pack(fill="x", pady=(10, 2))

    def _field(self, parent, label, value):
        row = tk.Frame(parent, bg=t.BG_DARK)
        row.pack(fill="x")
        tk.Label(
            row, text=f"{label}:", bg=t.BG_DARK, fg=t.FG_GRAY,
            font=t.FONT_MONO, width=10, anchor="w",
        ).pack(side="left")
        tk.Label(
            row, text=value, bg=t.BG_DARK, fg=t.FG_TEXT,
            font=t.FONT_MONO_BOLD, anchor="w",
        ).pack(side="left")


# Status bar

class StatsBar(tk.Frame):
    """One-line TIME / SCORE / RENT / STREAK strip with an update() method."""

    def __init__(self, parent):
        super().__init__(parent, bg=t.BG_PANEL, bd=1, relief="ridge")
        self._time = self._cell("TIME", "05:00")
        self._score = self._cell("SCORE", "0")
        self._rent = self._cell("RENT", "10")
        self._streak = self._cell("STREAK", "0")

    def _cell(self, label, value):
        frame = tk.Frame(self, bg=t.BG_PANEL)
        frame.pack(side="left", expand=True, fill="x", padx=8, pady=6)
        tk.Label(
            frame, text=label, bg=t.BG_PANEL, fg=t.FG_GRAY, font=t.FONT_LABEL,
        ).pack(side="left", padx=(0, 6))
        value_label = tk.Label(
            frame, text=value, bg=t.BG_PANEL, fg=t.FG_TEXT, font=t.FONT_MONO_BOLD,
        )
        value_label.pack(side="left")
        return value_label

    def update(self, state, clock):
        """Refresh all four cells from the live state and clock."""
        remaining = clock.time_remaining()
        self._time.config(
            text=clock.format_remaining(),
            fg=t.FG_RED if remaining < 30 else t.FG_GREEN,
        )
        self._score.config(text=str(state.score), fg=t.FG_TEAL)
        self._rent.config(text=str(state.rent), fg=t.FG_RUST)
        self._streak.config(
            text=str(state.consecutive_errors),
            fg=t.FG_RED if state.consecutive_errors >= 2 else t.FG_GRAY,
        )


# Feedback banner

class FeedbackBanner(tk.Frame):
    """A colored verdict banner: correct / incorrect / moral / bribe."""

    def __init__(self, parent):
        super().__init__(parent, bg=t.BG_DARK)
        self._title = tk.Label(self, bg=t.BG_DARK, font=t.FONT_SUBHEADER)
        self._title.pack(fill="x", padx=12)
        self._body = tk.Label(
            self, bg=t.BG_DARK, font=t.FONT_MONO, justify="left",
            anchor="w", wraplength=860,
        )
        self._body.pack(fill="x", padx=12)

    def _set(self, title, title_color, body, body_color):
        self._title.config(text=title, fg=title_color)
        self._body.config(text=body, fg=body_color)

    def correct(self, reason):
        self._set("✓ CORRECT", t.FG_GREEN, reason, t.FG_TEXT)

    def incorrect(self, reason, rent_change, action):
        note = "wrongful detention" if action == "detain" else f"wrongful {action}"
        body = reason
        if rent_change:
            body = f"{reason}\n({rent_change:+d} rent, {note})"
        self._set("✗ INCORRECT", t.FG_RED, body, t.FG_TEXT)

    def moral(self, reason):
        self._set("MORAL CHOICE — STATE LOGS AN ERROR", t.FG_PURPLE, reason, t.FG_PURPLE)

    def bribe(self):
        self._set(
            "BRIBE ACCEPTED",
            t.FG_YELLOW,
            "+2 rent. The traveler walks through. Your case ledger no "
            "longer balances perfectly.",
            t.FG_YELLOW,
        )

    def clear(self):
        self._title.config(text="")
        self._body.config(text="")


# Interrogation dialog

class InterrogationDialog(tk.Toplevel):
    """
    Modal question picker.

    on_pick(index) is expected to perform the domain work (session.ask, time
    cost, contradiction detection) and return a (question, contradiction_text)
    tuple, which this dialog then displays. Bribe acceptance is routed back to
    the main window via on_bribe_accept so it can close the case.
    """

    def __init__(self, parent, traveler, session, on_pick,
                 on_bribe_accept=None, on_close=None):
        super().__init__(parent, bg=t.BG_DARK)
        self.title("INTERROGATION")
        self.geometry("680x560")
        self.configure(padx=16, pady=16)
        self.traveler = traveler
        self.session = session
        self.on_pick = on_pick
        self.on_bribe_accept = on_bribe_accept
        self.on_close = on_close
        self._question_buttons = []

        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._close)

        self._header = tk.Label(
            self, bg=t.BG_DARK, fg=t.FG_PURPLE, font=t.FONT_SUBHEADER,
        )
        self._header.pack(fill="x", pady=(0, 10))

        self._button_box = tk.Frame(self, bg=t.BG_DARK)
        self._button_box.pack(fill="x")
        for i, question in enumerate(session.available_questions):
            btn = tk.Button(
                self._button_box,
                text=f"{i + 1}. {question.question_text}",
                anchor="w",
                justify="left",
                wraplength=600,
                command=lambda idx=i: self._pick(idx),
            )
            t.style_button(btn, fg=t.FG_PURPLE)
            btn.pack(fill="x", pady=3)
            self._question_buttons.append(btn)

        # Answer + contradiction display
        self._answer_title = tk.Label(self, bg=t.BG_DARK, fg=t.FG_TEAL, font=t.FONT_LABEL)
        self._answer_title.pack(fill="x", pady=(14, 2))
        self._answer = tk.Label(
            self, bg=t.BG_DARK, fg=t.FG_TEXT, font=t.FONT_MONO,
            justify="left", anchor="w", wraplength=640,
        )
        self._answer.pack(fill="x")
        self._contradiction = tk.Label(
            self, bg=t.BG_DARK, fg=t.FG_RED, font=t.FONT_MONO,
            justify="left", anchor="w", wraplength=640,
        )
        self._contradiction.pack(fill="x", pady=(4, 0))

        # Bribe prompt (hidden until a bribe question is asked)
        self._bribe_box = tk.Frame(self, bg=t.BG_DARK)

        # Footer
        footer = tk.Frame(self, bg=t.BG_DARK)
        footer.pack(side="bottom", fill="x", pady=(12, 0))
        back = tk.Button(footer, text="[B] Back to actions", command=self._close)
        t.style_button(back, fg=t.FG_GRAY)
        back.pack(side="right")

        self._refresh()

    def _refresh(self):
        """Sync header and button states with the session budget."""
        self._header.config(
            text=f"INTERROGATION — {self.session.remaining_questions()} QUESTIONS LEFT"
        )
        can_ask = self.session.can_ask_more()
        for i, btn in enumerate(self._question_buttons):
            question = self.session.available_questions[i]
            if i in self.session.asked_indices:
                btn.config(
                    state="disabled",
                    text=f"[done] {i + 1}. {question.question_text}",
                    disabledforeground=t.FG_GRAY,
                )
            elif not can_ask:
                btn.config(state="disabled", disabledforeground=t.FG_GRAY)
            else:
                btn.config(state="normal")

    def _pick(self, index):
        result = self.on_pick(index)
        if result is None:
            return
        question, contradiction_text = result

        self._answer_title.config(text=f"{self.traveler.document.name} ANSWERS:")
        self._answer.config(text=f"“{question.answer_text}”")

        if contradiction_text or question.has_contradiction():
            warning = (
                contradiction_text
                or question.contradiction_flag
                or "Answer contradicts the documents."
            )
            self._contradiction.config(text=f"⚠ CONTRADICTION: {warning}")
        else:
            self._contradiction.config(text="")

        if question.is_bribe_offer:
            self._show_bribe_prompt()

        self._refresh()

    def _show_bribe_prompt(self):
        for child in self._bribe_box.winfo_children():
            child.destroy()
        self._bribe_box.pack(fill="x", pady=(10, 0))
        prompt = tk.Label(
            self._bribe_box, text="A bribe is on the table.",
            bg=t.BG_DARK, fg=t.FG_YELLOW, font=t.FONT_LABEL,
        )
        prompt.pack(anchor="w")
        yes = tk.Button(
            self._bribe_box, text="[Y] ACCEPT BRIBE (+2 rent)",
            command=self._accept_bribe,
        )
        t.style_button(yes, fg=t.FG_YELLOW)
        yes.pack(side="left", pady=4)
        no = tk.Button(self._bribe_box, text="[N] REFUSE", command=self._refuse_bribe)
        t.style_button(no, fg=t.FG_GRAY)
        no.pack(side="left", padx=8)

    def _accept_bribe(self):
        self.destroy()
        if self.on_bribe_accept:
            self.on_bribe_accept()

    def _refuse_bribe(self):
        self._bribe_box.pack_forget()

    def _close(self):
        self.destroy()
        if self.on_close:
            self.on_close()


# Note interstitial

class NoteDialog(tk.Toplevel):
    """The folded note pushed under the booth glass. on_choice('R'|'I')."""

    def __init__(self, parent, dialogue, on_choice):
        super().__init__(parent, bg=t.BG_DARK)
        self.title("...")
        self.geometry("520x460")
        self.configure(padx=16, pady=16)
        self.dialogue = dialogue
        self.on_choice = on_choice

        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: self._choose("I"))

        tk.Label(
            self,
            text="A slip of paper has been pushed under your booth glass.",
            bg=t.BG_DARK, fg=t.FG_GRAY, font=t.FONT_MONO_SMALL, wraplength=480,
        ).pack(pady=(0, 12))

        tk.Label(
            self,
            text="\n".join(dialogue["note"]["ascii_art"]),
            bg=t.BG_DARK, fg=t.FG_RUST, font=t.FONT_MONO, justify="center",
        ).pack(pady=8)

        self._buttons = tk.Frame(self, bg=t.BG_DARK)
        self._buttons.pack(pady=16)
        read = tk.Button(
            self._buttons, text="[R] READ NOTE (-5s)",
            command=lambda: self._choose("R"),
        )
        t.style_button(read, fg=t.FG_YELLOW)
        read.pack(side="left", padx=6)
        ignore = tk.Button(
            self._buttons, text="[I] IGNORE", command=lambda: self._choose("I"),
        )
        t.style_button(ignore, fg=t.FG_GRAY)
        ignore.pack(side="left", padx=6)

        self._content = tk.Label(
            self, bg=t.BG_DARK, fg=t.FG_RUST, font=t.FONT_MONO,
            justify="center", wraplength=480,
        )

    def _choose(self, choice):
        # Let the main window apply the domain effect (mark read, time cost).
        self.on_choice(choice)
        if choice == "R":
            self._buttons.destroy()
            self._content.config(text=self.dialogue["note"]["content"])
            self._content.pack(pady=10)
            cont = tk.Button(self, text="Continue", command=self.destroy)
            t.style_button(cont, fg=t.FG_RUST)
            cont.pack(pady=8)
        else:
            self.destroy()


# Arrest window

class ArrestWindow(tk.Toplevel):
    """Halmos arrives. Portrait, then speech typed out, then ACCEPT YOUR FATE."""

    CHAR_DELAY_MS = 18

    def __init__(self, parent, state, dialogue, on_accept=None):
        super().__init__(parent, bg=t.BG_DARK)
        self.title("INTERNAL AFFAIRS")
        self.geometry("760x640")
        self.configure(padx=16, pady=16)
        self.on_accept = on_accept

        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: None)  # no escape until accepted

        tk.Label(
            self,
            text="\n".join(dialogue["halmos_portrait"]),
            bg=t.BG_DARK, fg=t.FG_RED, font=t.FONT_MONO, justify="center",
        ).pack(pady=(0, 8))

        tk.Label(
            self, text="INSPECTOR HALMOS — INTERNAL AFFAIRS",
            bg=t.BG_DARK, fg=t.FG_RED, font=t.FONT_SUBHEADER,
        ).pack(pady=(0, 10))

        self._text = tk.Text(
            self, bg=t.BG_PANEL, fg=t.FG_RUST, font=t.FONT_MONO,
            wrap="word", height=14, bd=0, padx=12, pady=12,
            highlightthickness=1, highlightbackground=t.FG_GRAY,
        )
        self._text.pack(fill="both", expand=True)
        self._text.config(state="disabled")

        self._accept = tk.Button(
            self, text="ACCEPT YOUR FATE", state="disabled", command=self._do_accept,
        )
        t.style_button(self._accept, fg=t.FG_RED)
        self._accept.pack(pady=(12, 0))

        # Build the full speech, then type it character by character.
        self._full_text = "\n".join(generate_review_speech(state, dialogue))
        self._index = 0
        self.after(400, self._type_next)

    def _type_next(self):
        if self._index < len(self._full_text):
            self._text.config(state="normal")
            self._text.insert("end", self._full_text[self._index])
            self._text.see("end")
            self._text.config(state="disabled")
            self._index += 1
            self.after(self.CHAR_DELAY_MS, self._type_next)
        else:
            self._accept.config(state="normal")

    def _do_accept(self):
        self.destroy()
        if self.on_accept:
            self.on_accept()


# Ending window

class EndingWindow(tk.Toplevel):
    """End-of-shift summary: ending narrative + final score, then Exit."""

    def __init__(self, parent, shift_result, dialogue, on_exit=None):
        super().__init__(parent, bg=t.BG_DARK)
        self.title("END OF SHIFT")
        self.geometry("760x600")
        self.configure(padx=16, pady=16)
        self.on_exit = on_exit

        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._do_exit)

        tk.Label(
            self, text="END OF SHIFT", bg=t.BG_DARK, fg=t.FG_RUST, font=t.FONT_HEADER,
        ).pack(pady=(0, 16))

        ending_lines = dialogue["endings"].get(shift_result.ending_key, [])
        narrative = "\n".join(ending_lines).strip()
        if narrative:
            tk.Label(
                self, text=narrative, bg=t.BG_DARK, fg=t.FG_TEXT,
                font=t.FONT_MONO, justify="left", wraplength=700,
            ).pack(fill="x", pady=(0, 16))

        summary = tk.Frame(self, bg=t.BG_PANEL, bd=1, relief="ridge")
        summary.pack(fill="x", pady=8)
        tk.Label(
            summary,
            text=f"FINAL SCORE: {shift_result.score} / {shift_result.total_travelers}",
            bg=t.BG_PANEL, fg=t.FG_RUST, font=t.FONT_SUBHEADER,
        ).pack(anchor="w", padx=12, pady=(8, 2))
        tk.Label(
            summary,
            text=(
                f"accuracy {shift_result.accuracy_pct}%   "
                f"rent remaining {shift_result.rent_remaining}   "
                f"errors {shift_result.total_errors}"
            ),
            bg=t.BG_PANEL, fg=t.FG_GRAY, font=t.FONT_MONO,
        ).pack(anchor="w", padx=12, pady=(0, 8))

        exit_btn = tk.Button(self, text="Exit", command=self._do_exit)
        t.style_button(exit_btn, fg=t.FG_RUST)
        exit_btn.pack(pady=(16, 0))

    def _do_exit(self):
        self.destroy()
        if self.on_exit:
            self.on_exit()
