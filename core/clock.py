"""
Real-time shift clock for THRESHOLD.

Runs the 2:30 countdown iun a background thread so the main game loop can display UI
and acept input while time ticks independently. When time hits zero, the clock sets
'is_expired' flag that main loop checks between actions.

The clock supports manual deduction (used when the player interrogates or reads the note
- each action costs seconds beyond the natural decay)/

"""

import threading

from exceptions import ShiftExpiredError


# Module-level constants

DEFAULT_SHIFT_DURATION_SECONDS = 300 # 5:00
TICK_INTERVAL_SECONDS = 1            # how often the timer thread updates.



class ShiftClock:
    """A real-time countdown clock for one shift."""

    def __init__(self, duration_seconds=DEFAULT_SHIFT_DURATION_SECONDS):
        if not isinstance(duration_seconds, int) or isinstance(duration_seconds,bool):
            raise TypeError(
                f"duration_seconds must be an int, got '{type(duration_seconds).__name__}'"
            )

        if duration_seconds <= 0:
            raise ValueError("duration_seconds must be positive.")
        

        self._time_remaining = duration_seconds
        self._is_running = False
        self._is_expired = False
        self._thread = None
        self._stop_event = threading.Event()

    
    # Public interface

    def start(self):
        """Begin the countdown, Spawns a backgroudn thread."""
        if self._is_running:
            return # already started, no-operations.
        
        self._is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target = self._tick_loop, daemon = True)
        self._thread.start()

    
    def stop(self):
        """Halth the countdown. Safe to call multiple times."""
        if not self._is_running:
            return
        
        self._is_running = False
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

        
    def time_remaining(self):
        """Return the current seconds remaining (never negative)."""
        return max(0, self._time_remaining)
        
    def consume(self, seconds):
        """
        Manually deduct seconds from the clock.
        
        Used when the player takes a costly action (interrogation, reading the note).
        Clamps at 0 — never goes negative.
        """
        if not isinstance(seconds, int) or isinstance(seconds, bool):
            raise TypeError(
                f"seconds must be an int, got {type(seconds).__name__}"
            )
        if seconds < 0:
            raise ValueError("seconds cannot be negative")
        self._time_remaining = max(0, self._time_remaining - seconds)
        if self._time_remaining <= 0:
            self._mark_expired()
    

    def is_expired(self):
        """True if the clock has hit zero."""
        return self._is_expired
    
    def raise_if_expired(self):
        """Convenience: raise ShiftExpiredError if the clock has run out."""
        if self._is_expired:
            raise ShiftExpiredError("Shift clock has expired.")
        

    def format_remaining(self):
        """Return the time as 'MM:SS' string for the UI."""
        remaining = self.time_remaining()
        minutes = remaining // 60
        seconds = remaining % 60
        return f"{minutes:02d}:{seconds:02d}"
    


    # Private internals

    def _tick_loop(self):
        """The backgroudn thread's loop. Decrements time once per second"""

        while not self._stop_event.is_set():
            # Use wait() with timeout instead of sleep() so we can be interrupted by stop() cleanly
            if self._stop_event.wait(timeout=TICK_INTERVAL_SECONDS):
                break
            self._time_remaining -= TICK_INTERVAL_SECONDS
            if self._time_remaining <= 0:
                self._mark_expired()
                break

    
    def _mark_expired(self):
        """Internal: flag the clock as expired and halt."""
        self._time_remaining = 0
        self._is_expired = True
        self._is_running = False

    

    def __repr__(self):
        status = "running" if self._is_running else "stopped"
        return (
        f"ShiftClock(remaining={self.time_remaining()}s, "
        f"status={status}, expired={self._is_expired})"
        )
