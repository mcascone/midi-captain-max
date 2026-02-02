"""
Mock displayio module - simulates CircuitPython display system.
"""


def release_displays():
    """Release all displays (no-op in mock)."""
    pass


class Bitmap:
    """Mock bitmap for display."""
    
    def __init__(self, width, height, value_count):
        self.width = width
        self.height = height
        self.value_count = value_count
        self._data = [[0] * width for _ in range(height)]
    
    def __setitem__(self, key, value):
        x, y = key
        self._data[y][x] = value
    
    def __getitem__(self, key):
        x, y = key
        return self._data[y][x]


class Palette:
    """Mock color palette."""
    
    def __init__(self, count):
        self._colors = [0] * count
    
    def __setitem__(self, index, color):
        self._colors[index] = color
    
    def __getitem__(self, index):
        return self._colors[index]
    
    def __len__(self):
        return len(self._colors)


class TileGrid:
    """Mock tile grid for display."""
    
    def __init__(self, bitmap, *, pixel_shader, x=0, y=0):
        self.bitmap = bitmap
        self.pixel_shader = pixel_shader
        self.x = x
        self.y = y


class Group:
    """Mock display group (container for display elements)."""
    
    def __init__(self, scale=1, x=0, y=0):
        self.scale = scale
        self.x = x
        self.y = y
        self._items = []
    
    def append(self, item):
        self._items.append(item)
    
    def remove(self, item):
        self._items.remove(item)
    
    def __len__(self):
        return len(self._items)
    
    def __getitem__(self, index):
        return self._items[index]
    
    def __setitem__(self, index, value):
        self._items[index] = value


class FourWire:
    """Mock SPI display bus."""
    
    def __init__(self, spi, *, command, chip_select, reset=None, baudrate=24000000):
        self.spi = spi
        self.command = command
        self.chip_select = chip_select
        self.reset = reset
        self.baudrate = baudrate
