# coding=utf-8
from _collections_abc import Iterable as IterableABC
from itertools import tee
from typing import Iterable


def pipe(func, *args, **kwargs):
    return PipeValue(func(*args, **kwargs))


class PipeValue:
    def __init__(self, value):
        self.value = value

    def then(self, func, *args, **kwargs):
        return PipeValue(func(self.value, *args, **kwargs))

    def then_post(self, func, *args, **kwargs):
        return PipeValue(func(*args, self.value, **kwargs))

    def then_as(self, func, key, *args, **kwargs):
        kwargs[key] = self.value
        return PipeValue(func(*args, **kwargs))


def do_if(boolVal, func):
    if boolVal:
        return func
    else:
        return _passThroughFirst


def _passThroughFirst(val, *args, **kwargs):
    return val


class Stream:
    def __init__(self, iterable: Iterable):
        if isinstance(iterable, Stream):
            self.iterable = iterable.iterable
        else:
            self.iterable = iterable

    def map(self, func):
        return Stream(map(func, self.iterable))

    def filter(self, func):
        return Stream(filter(func, self.iterable))

    def zip(self, *others):
        return Stream(zip(self.iterable, *(other.iterable for other in others)))

    def tee(self):
        iters = tee(self.iterable)
        return (Stream(iter) for iter in iters)

    def pipe(self, value):
        intermediate = value
        for func in self.iterable:
            intermediate = func(intermediate)
        return intermediate

    def skip_first(self):
        try:
            temp = self.iterable
            next(iter(temp))
            return Stream(temp)
        except StopIteration:
            return self

    def __iter__(self):
        return iter(self.iterable)

    @property
    def first(self):
        return next(iter(self.iterable))


IterableABC.register(Stream)
