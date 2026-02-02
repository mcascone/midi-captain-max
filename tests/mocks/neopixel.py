"""
Mock neopixel module - simulates NeoPixel LED strips.
"""


class NeoPixel:
    """Mock NeoPixel strip for testing."""
    
    # Fake constants matching real library
    RGB = "RGB"
    GRB = "GRB"
    RGBW = "RGBW"
    GRBW = "GRBW"
    
    def __init__(self, pin, n, *, brightness=1.0, auto_write=True, pixel_order=None):
        self.pin = pin
        self.n = n
        self.brightness = brightness
        self.auto_write = auto_write
        self.pixel_order = pixel_order or self.GRB
        self._pixels = [(0, 0, 0)] * n
    
    def __setitem__(self, index, color):
        if isinstance(index, slice):
            indices = range(*index.indices(self.n))
            if not hasattr(color, '__iter__') or isinstance(color, tuple):
                # Single color for all
                for i in indices:
                    self._pixels[i] = color
            else:
                # Iterable of colors
                for i, c in zip(indices, color):
                    self._pixels[i] = c
        else:
            self._pixels[index] = color
        if self.auto_write:
            self.show()
    
    def __getitem__(self, index):
        return self._pixels[index]
    
    def __len__(self):
        return self.n
    
    def fill(self, color):
        """Fill all pixels with a color."""
        self._pixels = [color] * self.n
        if self.auto_write:
            self.show()
    
    def show(self):
        """Update the pixels (no-op in mock)."""
        pass
    
    def deinit(self):
        """Release resources."""
        pass
    
    def get_all_colors(self):
        """Test helper: get all pixel colors."""
        return list(self._pixels)
