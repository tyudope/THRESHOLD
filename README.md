# THRESHOLD

THRESHOLD is a cyberpunk customs game inspired by *Papers, Please*. You play
Inspector Selim-X, working Gate 9 of New Astrakov, a sealed city-state in 2077.
You get one real-time 5:00 shift to process five travelers. Read their papers
against the day's State directives, lean on the suspicious ones, and decide
whether to approve, deny, or detain each of them. Every mistake costs you rent
and goes on your record. How the shift ends depends on how you do: you either
get PROMOTED, just CONTINUE THE SHIFT, or end up ARRESTED. That last one flips
the whole thing around. Inspector Halmos shows up, reads your own bad calls
back to you, and there's nothing left to do but take it.

## Screenshots

![Title screen](docs/threshold-title.png)

![Traveler interrogation](docs/threshold-traveler.png)

![Inspector Halmos arrest sequence](docs/threshold-arrest.png)

## How to run

There are two ways to play. Both need Python 3.10 or newer.

### CLI version (works in any terminal)

```bash
python3 main.py
```

No dependencies, just the standard library. Your terminal needs to handle ANSI
colors, which any modern Linux or macOS terminal does (on Windows, use Windows
Terminal). Polish characters render fine as long as the terminal is UTF-8.

### GUI version (tkinter)

```bash
python3 main_gui.py
```

You'll need a Python build that includes tkinter. The standard `python3` on
Ubuntu, the system Python on macOS, and the Windows installer all ship with it.
Some pyenv-built interpreters leave it out. If you get `ModuleNotFoundError: No
module named '_tkinter'`, run it with a system Python or rebuild your
interpreter against Tcl/Tk.

## Gameplay

- One shift, five travelers, a 5:00 clock counting down the whole time.
- Four things you can do with each traveler: Approve, Deny, Detain, or
  Interrogate (up to two questions each, 15 seconds a question).
- A note shows up between traveler one and two. Read it (costs 5 seconds) or
  skip it. Your choice changes Halmos's last line if you get arrested.
- After each verdict, the reason it was right, wrong, or a moral slip stays on
  screen for 8 seconds before the next traveler steps up, so you can actually
  read why.
- The wounded refugee, Orel Thane: the rules say deny, but you might not want
  to. Approving him costs less rent than a normal mistake, but it still counts
  against you.
- The bribe, Ven Narith: take it on his third question for +2 rent and a
  darker promoted ending.
- Three wrong calls in a row, or five total, and you're flagged. Halmos reads
  your mistakes out loud and you have to ACCEPT YOUR FATE.

## Architecture

- **exceptions.py**: the custom exception hierarchy. One `ThresholdError` base,
  with validation errors and control-flow signals underneath it.
- **models/**: plain data classes that validate themselves at construction
  (Traveler/Document/Permit, Directive/RuleSet, Question/InterrogationSession,
  ShiftState/WrongVerdict).
- **core/**: the actual game logic. The validator (rule engine), the lie
  detector (regex-based contradiction checks), the clock (a threaded real-time
  countdown), internal_affairs (the arrest sequence, built on a generator),
  verdict (end-of-shift scoring), and catalog (the JSON loader).
- **storage/**: a small, generic JSON repository and serializer pair.
- **data/**: all the game content as JSON (travelers, directives, dialogue).
- **cli/**: the terminal side. Theme constants, a couple of custom decorators
  (`@log_action`, `@reveal_slowly`), pure rendering functions, and the main
  loop with match-case dispatch.
- **gui/**: the tkinter side. Shared theme constants, reusable widgets, and a
  main window that drives the same flow as the CLI.

Both front ends run on the same domain code. None of the game rules are copied
between `cli/` and `gui/`.

## Key design decisions

- **Composition over inheritance**: a Traveler has a Document and a Permit
  instead of subclassing them.
- **Validation at the boundary**: constructors reject bad data up front, so the
  rest of the code can trust whatever it gets handed.
- **Functional core, imperative shell**: the validator and lie detector are
  pure functions. `ShiftState` is the only thing that mutates.
- **One sealed exception root**: everything hangs off `ThresholdError`, which
  keeps the top-level error handling simple.
- **Dispatch table for rules**: `RULE_CHECKERS` maps each `rule_id` to its
  checker function, so adding a rule is a one-line change.
- **A generator for the arrest speech**: `generate_review_speech` yields its
  lines lazily, so the CLI and GUI can each pace it their own way.
- **Two front ends, one set of rules**: the GUI reuses every `core/` and
  `models/` module without reimplementing anything.

## Python features used

- Classes with `__init__` validation, `__repr__`, and methods.
- A custom exception hierarchy.
- Generators (`yield`, `yield from`).
- Decorators, including parameterized ones and `@functools.wraps`.
- Regular expressions: compiled patterns, `re.IGNORECASE`, `\b` word boundaries.
- List, dict, and set comprehensions.
- Lambdas for `sorted(key=...)`.
- `match-case` for action dispatch.
- `with open(...)` context managers for file I/O.
- JSON serialization with `ensure_ascii=False` for UTF-8.
- `pathlib.Path` for portable paths.
- `threading.Thread` and `threading.Event` for the background clock.
- `tkinter` for the GUI: `Tk`/`Toplevel`, `grid`/`pack`, `after()`-based
  scheduling, and `grab_set()` for modal dialogs.

## Project conventions

- All file I/O is UTF-8 with `ensure_ascii=False`, so the Polish characters in
  sector names like POZNAŃ and KRAKÓW show up correctly.
- Action logging goes to `data/actions.log` through the `@log_action` decorator
  on the game-entry functions.
