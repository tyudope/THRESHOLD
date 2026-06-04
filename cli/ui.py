# cli/ui.py
"""
Pure rendering layer for THRESHOLD.

Every function here builds and prints one screen or component. Nothing in
this module makes a game-logic decision or reads input — it only takes the
objects it needs and turns them into colored text. All game flow lives in
cli/menu.py; all theming lives in cli/theme.py.
"""

from cli import theme
from cli.decorators import reveal_slowly
from core.internal_affairs import generate_review_speech


WIDTH = 60


# Title / intro screens

def render_title_screen():
    """Big THRESHOLD banner with subtitle and a press-Enter prompt."""
    theme.clear_screen()
    banner = [
        "  ████████ ██   ██ ██████  ███████ ███████ ██   ██  ██████  ██     ██████  ",
        "     ██    ██   ██ ██   ██ ██      ██      ██   ██ ██    ██ ██     ██   ██ ",
        "     ██    ███████ ██████  █████   ███████ ███████ ██    ██ ██     ██   ██ ",
        "     ██    ██   ██ ██   ██ ██           ██ ██   ██ ██    ██ ██     ██   ██ ",
        "     ██    ██   ██ ██   ██ ███████ ███████ ██   ██  ██████  ██████ ██████  ",
    ]
    print()
    for line in banner:
        print(theme.colored(line, theme.RUST))
    print()
    print(theme.colored("NEW ASTRAKOV CUSTOMS · GATE 9".center(WIDTH), theme.CYAN))
    print()
    print(theme.dim("The State watches itself through eyes like yours.".center(WIDTH)))
    print()
    print(theme.colored("Press Enter to begin".center(WIDTH), theme.GREEN))
    print()


# Directives

def render_directives(ruleset):
    """List today's directives — critical ones in red."""
    print(theme.colored(theme.header(f"DIRECTIVE FOR TODAY — Day {ruleset.day}", WIDTH), theme.RUST))
    for directive in ruleset.directives:
        label = f"{directive.number:02d}. {directive.text}"
        if directive.is_critical:
            print(theme.colored(f"  {label}", theme.RED))
        else:
            print(f"  {theme.dim(f'{directive.number:02d}.')} {directive.text}")
    print(theme.colored(theme.separator(WIDTH), theme.GRAY))


# Traveler card

def render_traveler_card(traveler, case_number, total_cases):
    """Two-column traveler card: portrait left, document fields right."""
    doc = traveler.document
    print(theme.colored(theme.header(f"TRAVELER {case_number} OF {total_cases}", WIDTH), theme.CYAN))
    print()

    # Build the right-hand document column as a list of lines.
    info_lines = [
        theme.colored("── IDENTITY ──", theme.GRAY),
        f"{theme.dim('Name:')}   {theme.bold(doc.name)}",
        f"{theme.dim('Age:')}    {doc.age}",
        f"{theme.dim('Sector:')} {doc.sector}",
        f"{theme.dim('Nation:')} {doc.nationality}",
        f"{theme.dim('NID:')}    {doc.neural_id}",
        f"{theme.dim('Status:')} ID issued {doc.id_age_years}y ago",
    ]

    # Portrait column padded to a fixed width so the two columns align.
    portrait = traveler.portrait
    portrait_width = max((len(line) for line in portrait), default=0)
    rows = max(len(portrait), len(info_lines))

    for i in range(rows):
        left = portrait[i] if i < len(portrait) else ""
        left = theme.colored(left.ljust(portrait_width), theme.RUST)
        right = info_lines[i] if i < len(info_lines) else ""
        print(f"  {left}   {right}")

    print()

    # Travel manifest section
    print(theme.colored("── TRAVEL MANIFEST ──", theme.GRAY))
    if traveler.permit is not None:
        permit = traveler.permit
        print(f"  {theme.dim('Manifest:')} {permit.manifest_id}")
        print(f"  {theme.dim('Valid:')}    {permit.valid_from} → {permit.valid_to}")
        print(f"  {theme.dim('Sponsor:')}  {permit.sponsor}")
    else:
        print(theme.colored("  (none submitted)", theme.RED))

    print()

    # Stated purpose (italic-ish via dim)
    print(theme.colored("── STATED PURPOSE ──", theme.GRAY))
    print(f"  {theme.dim(traveler.stated_purpose)}")

    # Optional tell — a visual cue the player can read
    if traveler.tell:
        print()
        print(f"  {theme.dim('* ' + traveler.tell)}")

    print(theme.colored(theme.separator(WIDTH), theme.GRAY))


# Status bar

def render_stats_bar(state, clock):
    """One-line TIME | SCORE | RENT | STREAK status strip."""
    time_str = clock.format_remaining()
    time_color = theme.RED if clock.time_remaining() < 30 else theme.GREEN
    time_cell = f"TIME {theme.colored(time_str, time_color)}"

    score_cell = f"SCORE {theme.colored(str(state.score), theme.CYAN)}"
    rent_cell = f"RENT {theme.colored(str(state.rent), theme.RUST)}"

    streak_color = theme.RED if state.consecutive_errors >= 2 else theme.GRAY
    streak_cell = f"STREAK {theme.colored(str(state.consecutive_errors), streak_color)}"

    print(theme.colored(theme.separator(WIDTH), theme.GRAY))
    print(f" {time_cell}   {score_cell}   {rent_cell}   {streak_cell}")
    print(theme.colored(theme.separator(WIDTH), theme.GRAY))


# Action menus

def render_action_menu():
    """The four primary verdict actions."""
    print()
    print(
        f"  {theme.colored('[I]', theme.PURPLE)} INTERROGATE {theme.dim('(-15s)')}   "
        f"{theme.colored('[A]', theme.GREEN)} APPROVE   "
        f"{theme.colored('[D]', theme.YELLOW)} DENY   "
        f"{theme.colored('[X]', theme.RED)} DETAIN"
    )
    print()


def render_interrogation_menu(session, traveler):
    """List the available questions; asked ones are dimmed and disabled."""
    print()
    print(theme.colored(
        theme.header(f"INTERROGATION — {session.remaining_questions()} QUESTIONS LEFT", WIDTH),
        theme.PURPLE,
    ))
    for i, question in enumerate(session.available_questions):
        number = i + 1
        if i in session.asked_indices:
            print(f"  {theme.dim(f'[done] {number}. {question.question_text}')}")
        else:
            print(f"  {theme.colored(f'{number}.', theme.PURPLE)} {question.question_text}")
    print()
    print(f"  {theme.colored('[B]', theme.GRAY)} Back to actions")
    print()


def render_question_answer(traveler, question, contradiction_text=None):
    """Show the answer to one question, flag contradictions and bribe offers."""
    print()
    print(theme.colored(f"{traveler.document.name} ANSWERS:", theme.CYAN))
    print(f"  {theme.dim('“' + question.answer_text + '”')}")

    if contradiction_text or question.has_contradiction():
        warning = contradiction_text or question.contradiction_flag or "Answer contradicts the documents."
        print()
        print(theme.colored(f"  ⚠ CONTRADICTION: {warning}", theme.RED))

    if question.is_bribe_offer:
        print()
        print(theme.colored(
            "  [Y] ACCEPT BRIBE (+2 rent)   [N] REFUSE",
            theme.YELLOW,
        ))
    print()


# The note interstitial (between travelers 1 and 2)

def render_note_interstitial(dialogue):
    """Show the folded-note ASCII and the read/ignore prompt."""
    theme.clear_screen()
    print()
    print(theme.colored("A slip of paper has been pushed under your booth glass.".center(WIDTH), theme.GRAY))
    print()
    for line in dialogue["note"]["ascii_art"]:
        print(theme.colored(line.center(WIDTH), theme.RUST))
    print()
    print(theme.colored(
        "  [R] READ NOTE (-5s)   [I] IGNORE".center(WIDTH),
        theme.YELLOW,
    ))
    print()


def render_note_content(dialogue):
    """Reveal the note's text inside a box."""
    theme.clear_screen()
    print()
    content_lines = dialogue["note"]["content"].split("\n")
    print(theme.colored(theme.boxed(content_lines, WIDTH), theme.RUST))
    print()


# Verdict feedback

def render_verdict_feedback(correct, reason, action, rent_change):
    """Green CORRECT / red INCORRECT banner with the reason and rent delta."""
    print()
    if correct:
        print(theme.colored(theme.header("CORRECT", WIDTH), theme.GREEN))
    else:
        print(theme.colored(theme.header("INCORRECT", WIDTH), theme.RED))

    print(f"  {reason}")

    if not correct and rent_change:
        if action == "detain":
            note = "wrongful detention"
        else:
            note = f"wrongful {action}"
        print(theme.colored(f"  ({rent_change:+d} rent, {note})", theme.RED))
    print()


def render_moral_choice_feedback(reason):
    """Purple banner used when the player makes the documented moral violation."""
    print()
    print(theme.colored(theme.header("MORAL CHOICE — STATE LOGS AN ERROR", WIDTH), theme.PURPLE))
    print(f"  {theme.colored(reason, theme.PURPLE)}")
    print()


def render_bribe_taken_feedback():
    """Yellow banner shown after a bribe is accepted."""
    print()
    print(theme.colored(theme.header("BRIBE ACCEPTED", WIDTH), theme.YELLOW))
    print(theme.colored(
        "  +2 rent. The traveler walks through. Your case ledger no",
        theme.YELLOW,
    ))
    print(theme.colored("  longer balances perfectly.", theme.YELLOW))
    print()


# Arrest sequence (Internal Affairs)

@reveal_slowly(line_delay=0.7, char_delay=0.025)
def _speak_review(state, dialogue):
    """Generator wrapper so @reveal_slowly paces Halmos's speech dramatically."""
    yield from generate_review_speech(state, dialogue)


def render_arrest_sequence(state, dialogue):
    """Halmos arrives: portrait, header, then the slowly-revealed speech."""
    theme.clear_screen()
    print()
    print(theme.colored(theme.boxed(dialogue["halmos_portrait"], WIDTH), theme.RED))
    print()
    print(theme.colored(theme.header("INSPECTOR HALMOS — INTERNAL AFFAIRS", WIDTH), theme.RED))
    print()

    _speak_review(state, dialogue)

    print()
    print(theme.colored("Press Enter to ACCEPT YOUR FATE".center(WIDTH), theme.RED))


# Ending

def render_ending(shift_result, dialogue):
    """End-of-shift summary: ending narrative + final score and accuracy."""
    theme.clear_screen()
    print()
    print(theme.colored(theme.header("END OF SHIFT", WIDTH), theme.RUST))
    print()

    ending_lines = dialogue["endings"].get(shift_result.ending_key, [])
    for line in ending_lines:
        print(f"  {line}" if line else "")
    print()

    print(theme.colored(theme.separator(WIDTH), theme.GRAY))
    score_line = f"FINAL SCORE: {shift_result.score} / {shift_result.total_travelers}"
    print(f"  {theme.bold(score_line)}   {theme.dim(f'accuracy {shift_result.accuracy_pct}%')}")
    print(f"  {theme.dim(f'rent remaining: {shift_result.rent_remaining}   errors: {shift_result.total_errors}')}")
    print(theme.colored(theme.separator(WIDTH), theme.GRAY))
    print()
    print(theme.dim("Press Enter to exit.".center(WIDTH)))


# Error display

def render_error_message(message):
    """Red ERROR banner for clean (non-crashing) error display."""
    print()
    print(theme.colored(theme.header("ERROR", WIDTH), theme.RED))
    print(theme.colored(f"  {message}", theme.RED))
    print()
