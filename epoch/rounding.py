from typing import List
# Starting Data:
#


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
