# cli/theme.py
"""
ANSI colors and ASCII frame helpers for the THRESHOLD terminal UI.
"""

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Foreground colors (matched to the demo aesthetic)
RED = "\033[38;5;167m"          # warning / error / arrest
GREEN = "\033[38;5;108m"        # correct / approve
YELLOW = "\033[38;5;179m"       # caution / bribe
PURPLE = "\033[38;5;139m"       # interrogation
CYAN = "\033[38;5;109m"         # neutral info
GRAY = "\033[38;5;243m"         # dim labels
RUST = "\033[38;5;180m"         # main accent
TEAL = "\033[38;5;108m"         # verified


# ─────────────────────────────────────────────────────────────
# Style helpers
# ─────────────────────────────────────────────────────────────

def colored(text, color):
    """Wrap text in ANSI color codes."""
    return f"{color}{text}{RESET}"


def bold(text):
    return f"{BOLD}{text}{RESET}"


def dim(text):
    return f"{DIM}{text}{RESET}"


# ─────────────────────────────────────────────────────────────
# Frame helpers
# ─────────────────────────────────────────────────────────────

def header(text, width=60):
    """Render a centered header line with frame characters."""
    padding = max(0, (width - len(text) - 4) // 2)
    return f"{'═' * padding}[ {text} ]{'═' * padding}"


def separator(width=60, char="─"):
    """Render a horizontal separator line."""
    return char * width


def boxed(lines, width=60):
    """Wrap a list of lines in a simple ASCII box."""
    top = "┌" + ("─" * (width - 2)) + "┐"
    bottom = "└" + ("─" * (width - 2)) + "┘"
    boxed_lines = [top]
    for line in lines:
        padded = line.ljust(width - 4)
        boxed_lines.append(f"│ {padded} │")
    boxed_lines.append(bottom)
    return "\n".join(boxed_lines)


def clear_screen():
    """ANSI escape sequence to clear the screen and move cursor to top-left."""
    print("\033[2J\033[H", end="")