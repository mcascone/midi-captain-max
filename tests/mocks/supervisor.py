"""
Mock for CircuitPython's supervisor module.

Provides stub implementations of the supervisor attributes used by firmware:
  - supervisor.runtime.serial_bytes_available  (always False in tests)
  - supervisor.reload()                        (no-op)
  - supervisor.disable_autoreload()            (no-op)
"""


class _Runtime:
    serial_bytes_available = False


runtime = _Runtime()


def reload():
    """No-op stub — firmware calls this to soft-reset the device."""
    pass


def disable_autoreload():
    """No-op stub — called in boot.py to disable CircuitPython autoreload."""
    pass
