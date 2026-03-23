"""Mock NoteOn message."""

class NoteOn:
    """Mock MIDI Note On message."""
    def __init__(self, note, velocity=127, *, channel=None):
        self.note = note
        self.velocity = velocity
        self.channel = channel if channel is not None else 0
