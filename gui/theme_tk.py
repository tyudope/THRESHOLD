# gui/theme_tk.py
"""
Tkinter color and font constants for THRESHOLD.

These mirror the 256-color ANSI palette used by the CLI's cli/theme.py,
translated to hex so tkinter can render the same cyberpunk / 2077 look:
a near-black warm background with rust and dark-red accents, monospace
documents. All gui/ modules import their styling from here so the look
stays consistent.
"""

# Backgrounds (warm near-black, matching the CLI's dark terminal feel)
BG_DARK = "#140f0d"        # main window background
BG_PANEL = "#1f1815"       # raised panels (cards, bars)
BG_INPUT = "#2a211c"       # buttons / interactive surfaces

# Foreground accents - hex equivalents of the CLI's xterm-256 codes
FG_RUST = "#d7af87"        # xterm 180 - main accent
FG_RED = "#d75f5f"         # xterm 167 - warning / error / arrest
FG_GREEN = "#87af87"       # xterm 108 - correct / approve
FG_YELLOW = "#d7af5f"      # xterm 179 - caution / bribe
FG_PURPLE = "#af87af"      # xterm 139 - interrogation
FG_GRAY = "#767676"        # xterm 243 - dim labels
FG_TEAL = "#87af87"        # xterm 108 - verified
FG_TEXT = "#cbb8a6"        # default warm body text

# Fonts - monospace everywhere for the bureaucratic, terminal aesthetic
FONT_MONO = ("Courier New", 12)
FONT_MONO_SMALL = ("Courier New", 10)
FONT_MONO_BOLD = ("Courier New", 12, "bold")
FONT_HEADER = ("Courier New", 24, "bold")
FONT_SUBHEADER = ("Courier New", 14, "bold")
FONT_LABEL = ("Courier New", 11, "bold")
FONT_BUTTON = ("Courier New", 12, "bold")


def style_button(button, fg=FG_RUST):
    """Apply the shared dark/rust button styling in one place."""
    button.configure(
        bg=BG_INPUT,
        fg=fg,
        activebackground=FG_RUST,
        activeforeground=BG_DARK,
        relief="flat",
        bd=1,
        highlightthickness=1,
        highlightbackground=FG_GRAY,
        font=FONT_BUTTON,
        cursor="hand2",
        padx=10,
        pady=6,
    )
