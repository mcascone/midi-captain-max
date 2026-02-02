"""
Mock busio module - simulates CircuitPython bus I/O (SPI, I2C, UART).
"""


class SPI:
    """Mock SPI bus."""
    
    def __init__(self, clock, MOSI=None, MISO=None):
        self.clock = clock
        self.MOSI = MOSI
        self.MISO = MISO
        self._locked = False
    
    def try_lock(self):
        if self._locked:
            return False
        self._locked = True
        return True
    
    def unlock(self):
        self._locked = False
    
    def configure(self, *, baudrate=100000, polarity=0, phase=0, bits=8):
        pass
    
    def write(self, buffer, *, start=0, end=None):
        pass
    
    def readinto(self, buffer, *, start=0, end=None, write_value=0):
        pass
    
    def write_readinto(self, buffer_out, buffer_in, *, out_start=0, out_end=None, in_start=0, in_end=None):
        pass
    
    def deinit(self):
        pass


class I2C:
    """Mock I2C bus."""
    
    def __init__(self, scl, sda, *, frequency=100000):
        self.scl = scl
        self.sda = sda
        self.frequency = frequency
        self._locked = False
    
    def try_lock(self):
        if self._locked:
            return False
        self._locked = True
        return True
    
    def unlock(self):
        self._locked = False
    
    def scan(self):
        return []
    
    def deinit(self):
        pass


class UART:
    """Mock UART."""
    
    def __init__(self, tx=None, rx=None, *, baudrate=9600, bits=8, parity=None, stop=1, timeout=1):
        self.tx = tx
        self.rx = rx
        self.baudrate = baudrate
        self._buffer = bytearray()
    
    def read(self, nbytes=None):
        if nbytes is None:
            data = bytes(self._buffer)
            self._buffer.clear()
            return data
        data = bytes(self._buffer[:nbytes])
        self._buffer = self._buffer[nbytes:]
        return data
    
    def write(self, buf):
        return len(buf)
    
    @property
    def in_waiting(self):
        return len(self._buffer)
    
    def deinit(self):
        pass
