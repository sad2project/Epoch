# coding=utf-8
# Starting Data:
#
from functools import partial
from typing import Tuple, Callable

from .functions import *
from .time_tracking import *


def full_workflow(
        tlp_lines: Iterable[TLPLine],
        adjustment_lookup: Dict[TLP, int],
        do_travel_time: bool,
        do_first_time: bool,
        do_full_day: bool,
        plugins: Iterable[Callable[[AdjustedTLPDuration], AdjustedTLPDuration]]
        ) -> Iterable[AdjustedTLPDuration]:
    return Stream(plugins).pipe(
        pipe(basic_workflow, tlp_lines, adjustment_lookup)
        .then(do_if(do_travel_time, travel_time_adjustment))
        .then(do_if(do_first_time, first_time_adjustment))
        .then(do_if(do_full_day, full_day_adjustment)))


def travel_time_adjustment(adjusted_tlps):
    # TODO
    return adjusted_tlps


def first_time_adjustment(adjusted_tlps):
    # TODO
    # nonlocal adjustment_lookup

    return adjusted_tlps


def full_day_adjustment(adjusted_tlps):
    # TODO
    return adjusted_tlps


def basic_workflow(
        tlp_lines: Iterable[TLPLine],
        adjustment_lookup: Dict[TLP, int]
        ) -> Iterable[AdjustedTLPDuration]:
    return (pipe(times_to_durations, tlp_lines)
            .then(combine_tlp_durations)
            .then_post(add_adjustments, adjustment_lookup))


def times_to_durations(tlp_lines: Iterable[TLPLine]) -> Iterable[TLPDuration]:
    orig, offset = Stream(tlp_lines).tee()
    return (orig.zip(offset.skip_first())
            .map(_combine_to_duration))


def _combine_to_duration(times: Tuple[TLPLine, TLPLine]) -> TLPDuration:
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
    return Stream(tlps.items())


def add_adjustments(
        adj_lookup: Dict[TLP, int],
        tlp_durations: Iterable[TLPDuration]
        ) -> Iterable[AdjustedTLPDuration]:
    return (Stream(tlp_durations)
            .map(_add_adjustment(adj_lookup)))


# noinspection PyTypeChecker
def _add_adjustment(
        adj_lookup: Dict[TLP, int]
        ) -> Callable[[TLPDuration], AdjustedTLPDuration]:
    return partial(
        TLPDuration.with_adjustment_from,
        adjustment_lookup=adj_lookup)
