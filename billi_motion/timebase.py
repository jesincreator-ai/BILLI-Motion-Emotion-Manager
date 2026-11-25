"""Monotonic millisecond helpers compatible with MicroPython ticks wraparound."""
try:
    from time import ticks_add as _ticks_add
    from time import ticks_diff as _ticks_diff
except ImportError:
    def _ticks_add(value, delta):
        return int(value) + int(delta)

    def _ticks_diff(a, b):
        return int(a) - int(b)


def add_ms(value, delta):
    return _ticks_add(int(value), int(delta))


def diff_ms(a, b):
    return _ticks_diff(int(a), int(b))
