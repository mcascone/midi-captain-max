"""Mock SystemExclusive message."""

class SystemExclusive:
    """Mock MIDI System Exclusive message."""
    def __init__(self, manufacturer_id, data):
        """
        Args:
            manufacturer_id: List/tuple of manufacturer ID bytes (e.g., [0x7D])
            data: Bytes or bytearray of SysEx data payload
        
        Note: Real adafruit_midi expects positional arguments, not keyword args
        """
        self.manufacturer_id = manufacturer_id
        self.data = data
