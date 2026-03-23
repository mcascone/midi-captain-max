"""Mock NoteOff message."""

class NoteOff:
    """Mock MIDI Note Off message."""
    def __init__(self, note, velocity=0, *, channel=None):
        self.note = note
        self.velocity = velocity
        self.channel = channel if channel is not None else 0
