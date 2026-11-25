"""Fixed-capacity event queue; oldest event is discarded on overflow."""


class EventQueue:
    def __init__(self, capacity=16):
        capacity = int(capacity)
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self.capacity = capacity
        self._items = [None] * capacity
        self._head = 0
        self._size = 0

    def push(self, event):
        if self._size == self.capacity:
            self._items[self._head] = event
            self._head = (self._head + 1) % self.capacity
            return False
        index = (self._head + self._size) % self.capacity
        self._items[index] = event
        self._size += 1
        return True

    def pop(self):
        if self._size == 0:
            return None
        event = self._items[self._head]
        self._items[self._head] = None
        self._head = (self._head + 1) % self.capacity
        self._size -= 1
        return event

    def __len__(self):
        return self._size
