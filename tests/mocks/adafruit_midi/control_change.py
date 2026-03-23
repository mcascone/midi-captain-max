"""Mock ControlChange message."""

class ControlChange:
    """Mock MIDI Control Change message."""
    def __init__(self, control, value, *, channel=None):
        self.control = control
        self.value = value
        self.channel = channel if channel is not None else 0
