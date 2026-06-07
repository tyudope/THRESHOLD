# cli/decorators.py
"""
Custom decorators.

@log_action      logs game events to data/actions.log with a timestamp
@reveal_slowly   prints text character-by-character or line-by-line for drama
"""

import functools
import time
from datetime import datetime
from pathlib import Path


LOG_FILE = Path("data/actions.log")
DEFAULT_CHAR_DELAY = 0.02       # seconds per character
DEFAULT_LINE_DELAY = 0.6        # seconds between lines

# @log_action - simple decorator, no parameters

def log_action(func):
    """Decorator: logs each call of func to data/actions.log with timestamp."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Build a timestamp
        timestamp = datetime.now().isoformat(timespec="seconds")

        # Format the log line
        log_line = f"[{timestamp}] {func.__name__}(args={args}, kwargs={kwargs})\n"

        # Ensure data/ exists, append to log file
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)

        # Call the wrapped function and return its result
        result = func(*args, **kwargs)
        return result

    return wrapper


# @reveal_slowly(...) parameterized decorator (decorator factory)

def reveal_slowly(line_delay=DEFAULT_LINE_DELAY, char_delay=DEFAULT_CHAR_DELAY):
    """
    Parameterized decorator. Wraps a generator that yields strings -
    prints each yielded line character-by-character with delays.

    
    @reveal_slowly(line_delay=0.8, char_delay=0.03)
    def speak():
        yield "Inspector Selim-X."
        yield "..."
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # The wrapped function is a generator - get the generator object
            generator = func(*args, **kwargs)

            # Iterate over each yielded line
            for line in generator:
                # Print one character at a time with a small delay
                for char in line:
                    print(char, end="", flush=True)
                    time.sleep(char_delay)
                # Newline at the end of each yielded line
                print()
                # Pause between lines for dramatic effect
                time.sleep(line_delay)

        return wrapper

    return decorator