# coding=utf-8
from .time import *


undefined = object()


class TLP:
    def __init__(self,
                 tlp_code: int,
                 description: str,
                 customer: int=undefined,
                 product: int=undefined,
                 code: int=undefined,
                 slg: int=undefined,
                 dlg: int=undefined,
                 prj: int=undefined):
        self.tlp_code = tlp_code
        self.description = description
        self.customer = customer
        self.product = product
        self.code = code
        self.slg = slg
        self.dlg = dlg
        self.prj = prj

    def __eq__(self, other: 'TLP') -> bool:
        return (self._non_desc_components() == other._non_desc_components())

    def __hash__(self):
        return hash(self._non_desc_components())

    def _non_desc_components(self):
        return (self.tlp_code, self.customer, self.product, self.code, self.slg, self.dlg, self.prj)

    def __add__(self, other) -> 'TLP':
        if self != other:
            raise ValueError('Cannot add/combine two TLGs that have a different'
                             ' set of values (excluding description)')
        return TLP(
                self.tlp_code,
                self.description + "; " + other.description,
                self.customer,
                self.product,
                self.code,
                self.slg,
                self.dlg,
                self.prj)


class TLPLine:
    def __init__(self, tlp: TLP, time: Time):
        self.time = time
        self.tlp = tlp

    def to_next(self, next_line: 'TLPLine') -> 'TLPDuration':
        return TLPDuration(self.tlp, next_line.time.time_between(self.time))


class TLPDuration:
    def __init__(self, tlp: TLP, duration: Duration):
        self.duration = duration
        self.tlp = tlp

    def has_same_tlp_as(self, other: 'TLPDuration') -> bool:
        return self.tlp == other.tlp

    def with_accum_adjustment(
            self, adjustment: int) -> 'TLPDurationWithAdjustment':
        return TLPDurationWithAdjustment(
            self.tlp,
            self.duration.with_accumulated_adjustment(Minutes(adjustment)))

    def with_no_accum_adjustment(self) -> 'TLPDurationWithAdjustment':
        return self.with_accum_adjustment(0)

    def __add__(self, other: 'TLPDuration') -> 'TLPDuration':
        return TLPDuration(self.tlp + other.tlp, self.duration + other.duration)

    def __eq__(self, other) -> bool:
        return self.tlp == other.TLP

    def __hash__(self) -> int:
        return hash(self.tlp)


class TLPDurationWithAdjustment:
    def __init__(
            self, tlp: TLP, duration_with_adjustment: DurationWithAdjustment):
        self.tlp = tlp
        self.duration_with_adjustment = duration_with_adjustment


class AdjustedTLPDuration:
    def __init__(self, tlp: TLP, adjusted_duration: AdjustedDuration):
        self.tlp = tlp
        self.adjusted_duration = adjusted_duration

    def force_round_up(self):
        return AdjustedTLPDuration(
                self.tlp,
                self.adjusted_duration.force_round_up())

    def force_round_down(self):
        return AdjustedTLPDuration(
                self.tlp,
                self.adjusted_duration.force_round_down())

    def __gt__(self, other: 'AdjustedTLPDuration') -> bool:
        return self.adjusted_duration > other.adjusted_duration

    def __lt__(self, other: 'AdjustedTLPDuration') -> bool:
        return self.adjusted_duration < other.adjusted_duration
