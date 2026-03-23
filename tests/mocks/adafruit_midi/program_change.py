"""Mock ProgramChange message."""

class ProgramChange:
    """Mock MIDI Program Change message."""
    def __init__(self, patch, *, channel=None):
        self.patch = patch
        self.channel = channel if channel is not None else 0
