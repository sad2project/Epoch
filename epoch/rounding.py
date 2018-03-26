# coding=utf-8
# Starting Data:
#
from _collections_abc import Iterable as IterableABC
from itertools import tee
from typing import Iterable, Tuple

from .time_tracking import *


class Sequence:
    def __init__(self, iterable: Iterable):
        if isinstance(iterable, Sequence):
            self.iterable = iterable.iterable
        else:
            self.iterable = iterable

    def map(self, func):
        return Sequence(map(func, self.iterable))

    def filter(self, func):
        return Sequence(filter(func, self.iterable))

    def zip(self, *others):
        return Sequence(zip(self.iterable, *(other.iterable for other in others)))

    def tee(self):
        iters = tee(self.iterable)
        return (Sequence(iter) for iter in iters)

    def skip_first(self):
        try:
            temp = self.iterable
            next(iter(temp))
            return Sequence(temp)
        except StopIteration:
            return self

    def __iter__(self):
        return iter(self.iterable)

    @property
    def first(self):
        return next(iter(self.iterable))


IterableABC.register(Sequence)


def times_to_durations(tlp_lines: Iterable[TLPLine]) -> Iterable[TLPDuration]:
    orig, offset = Sequence(tlp_lines).tee()
    return (orig.zip(offset.skip_first())
            .map(_combine_to_duration))


def _combine_to_duration(times: Tuple[TLPLine,TLPLine]) -> TLPDuration:
    return times[0].to_next(times[1])


def combine_tlp_durations(
        tlp_durations: Iterable[TLPDuration]
        ) -> Iterable[TLPDuration]:
    tlps = {}
    for tlp_duration in tlp_durations:
        tlp = tlp_duration.tlp
        if tlp in tlps:
            tlps[tlp] += tlp_duration
        else:
            tlps[tlp] = tlp_duration
    return Sequence(tlps.items())
