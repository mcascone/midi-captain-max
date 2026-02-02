"""
Mock terminalio module - provides built-in terminal font.
"""


class MockFont:
    """Mock font object."""
    
    def __init__(self, name="FONT"):
        self.name = name
    
    def get_bounding_box(self):
        """Return (width, height, dx, dy) of font."""
        return (6, 12, 0, -10)


FONT = MockFont("terminalio.FONT")
