# main_gui.py
"""
THRESHOLD - GUI entry point.

A tkinter front end for the customs-interrogation game. Reuses the exact
same domain logic as the CLI (main.py); only the presentation differs.

    python3 main_gui.py
"""

from gui.main_window import GameWindow


if __name__ == "__main__":
    app = GameWindow()
    app.mainloop()
