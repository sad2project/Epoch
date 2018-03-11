from typing import List
# Starting Data:
#

# TODO: Create a Sequence so I can use the sequence/stream APIs as methods instead of normal
# ugly functions.

class Sequence:
    def __init__(self, iterable):
        self.iterable = iterable

    def map(self, func):
        return Sequence(map(func, self.iterable))

    def filter(self, func):
        return Sequence(filter(func, self.iterable))

    def __iter__(self):
        return iter(self.iterable)

    @property
    def first(self):
        return next(iter(self.iterable))


