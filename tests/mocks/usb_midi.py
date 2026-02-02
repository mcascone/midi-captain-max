"""
Mock usb_midi module - simulates CircuitPython USB MIDI.
"""


class MockMIDIPort:
    """Mock MIDI port for testing."""
    
    def __init__(self, name="Mock MIDI"):
        self.name = name
        self._sent = []
        self._received = []
    
    def write(self, data, length=None):
        """Write MIDI data to the port."""
        if length is None:
            length = len(data)
        self._sent.append(bytes(data[:length]))
    
    def read(self, length):
        """Read MIDI data from the port."""
        if not self._received:
            return None
        data = self._received.pop(0)
        return data[:length]
    
    # Test helpers
    def inject_midi(self, data):
        """Inject MIDI data to be read."""
        self._received.append(bytes(data))
    
    def get_sent(self):
        """Get all sent MIDI messages."""
        return list(self._sent)
    
    def clear(self):
        """Clear sent and received buffers."""
        self._sent.clear()
        self._received.clear()


# Default ports (as CircuitPython provides)
ports = (MockMIDIPort("MIDI In"), MockMIDIPort("MIDI Out"))
