"""Mock adafruit_midi module for testing."""

class MIDI:
    """Mock MIDI class."""
    def __init__(self, *args, **kwargs):
        self.out_channel = 0

    def send(self, msg):
        """Mock send - no-op."""
        pass

    def receive(self):
        """Mock receive - returns None."""
        return None
