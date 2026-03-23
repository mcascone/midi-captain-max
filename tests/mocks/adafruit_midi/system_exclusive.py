"""Mock SystemExclusive message."""

class SystemExclusive:
    """Mock MIDI System Exclusive message."""
    def __init__(self, manufacturer_id, data):
        """
        Args:
            manufacturer_id: List of manufacturer ID bytes (e.g., [0x7D])
            data: Bytes or bytearray of SysEx data payload
        """
        self.manufacturer_id = manufacturer_id
        self.data = data
