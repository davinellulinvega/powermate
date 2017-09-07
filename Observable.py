#!/usr/bin/python3
from collections import defaultdict


class Observable:
    def __init__(self):
        self._observers = defaultdict(list)

    def register(self, event_name, callback):
        if callable(callback) and not callback in self._observers[event_name]:
            self._observers[event_name].append(callback)

    def unregister(self, event_name, callback):
        try:
            self._observers[event_name].remove(callback)
        except ValueError:
            pass

    def unregister_all(self):
        self._observers = defaultdict(list)

    def listen(self):
        raise NotImplementedError("Implementation of method 'listen' missing.")
