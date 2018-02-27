from .rounding import Sequence
from ._time_parsing import *
from typing import Union, Callable


__all__ = ['Time', 'TLP', 'Timestamp', 'Duration', 'DurationWithAdjustment',
           'AdjustedDuration']


class Time:
    def __init__(self, hour: int, minute: int):
        self.hour = hour
        self.minute = minute

    @classmethod
    def from_user_time(cls, user_time: str, cutoff_config: Callable[[int], bool]):
        return cls(*parse_user_time(user_time, cutoff_config))

    @classmethod
    def now(cls) -> 'Time':
        return cls(*now())

    def __str__(self) -> str:
        return f'{self.hour}:{self.minute}'

    def __eq__(self, other: 'Time') -> bool:
        return (self.hour, self.minute) == (other.hour, other.minute)

    def __add__(self, other: int) -> 'Time':
        return Time(*fix_under_over(self.hour, self.minute + other))


undefined = object()


class TLP:
    def __init__(self,
                 tlp_code: int,
                 description: str,
                 customer:=undefined,
                 product=undefined,
                 code=undefined,
                 slg=undefined,
                 dlg=undefined,
                 prj=undefined):
        self.tlp_code = tlp_code
        self.description = description
        self.customer = customer
        self.product = product
        self.code = code
        self.slg = slg
        self.dlg = dlg
        self.prj = prj

    def __eq__(self, other: 'TLP'):
        return (self.tlp_code, self.customer, self.product, self.code,
                self.slg, self.dlg, self.prj) == \
               (other.tlp_code, other.customer, other.product, other.code,
                other.slg, other.dlg, other.prj)

    def __add__(self, other) -> 'TLP':
        if self != other:
            raise ValueError('Cannot add/combine two TLGs that have the same ' +
                             'set of values (excluding description)')
        return TLP(
                self.tlp_code,
                self.description + "; " + other.description,
                self.customer,
                self.product,
                self.code,
                self.slg,
                self.dlg,
                self.prj)


class Timestamp:
    def __init__(self, tlp: TLP, time: Time):
        self.time = time
        self.tlp = tlp

    def to(self, end_time):
        return Duration(self.tlp, end_time - self.time)


class DurationWithAdjustment:
    def __init__(self, tlp, duration, acc_adjustment):
        self.TLP = tlp
        self.duration = duration
        self.acc_adjustment = acc_adjustment
        self.adjustment = None

    @property
    def adjusted_duration(self):
        if self.adjustment is None:
            self.adjustment = _best_adjustment(
                    self.duration,
                    self.acc_adjustment)
        return self.duration + self.adjustment

    @property
    def new_acc_adjustment(self):
        if self.adjustment is None:
            self.adjustment = _best_adjustment(
                    self.duration,
                    self.acc_adjustment)
        return self.acc_adjustment + self.adjustment

    def do_best_adjustment(self):
        return self

    def force_round_up(self):
        adjustment_up, _ = _adjustments_to_nearest_15(self.duration)
        return AdjustedDuration(
                self.TLP,
                self.duration,
                adjustment_up,
                self.acc_adjustment)

    def force_round_down(self):
        _, adjustment_down = _adjustments_to_nearest_15(self.duration)
        return AdjustedDuration(
                self.TLP,
                self.duration,
                adjustment_down,
                self.acc_adjustment)

    @property
    def _comparison_key(self):
        return self.new_acc_adjustment, self.adjusted_duration

    def __gt__(self, other):
        return self._comparison_key > other._comparison_key

    def __lt__(self, other):
        return self._comparison_key < other._comparison_key


class Duration:
    def __init__(self, tlp: TLP, duration: int):
        self.duration = duration
        self.tlp = tlp

    def has_same_tlp_as(self, other: 'Duration') -> bool:
        return self.tlp == other.tlp

    def __add__(self, other: 'Duration') -> 'Duration':
        return Duration(self.tlp + other.tlp, self.duration + other.duration)

    def __eq__(self, other) -> bool:
        return self.tlp == other.TLP

    def __hash__(self) -> int:
        return hash(self.tlp)

    def and_accumulated_adjustment(self, adjustment: int) -> DurationWithAdjustment:
        return DurationWithAdjustment(self.tlp, self.duration, adjustment)

    def with_no_accumulated_adjustment(self) -> DurationWithAdjustment:
        return DurationWithAdjustment(self.tlp, self.duration, 0)


class AdjustedDuration:
    def __init__(self, TLP, old_duration, adjustment, acc_adjustment):
        self.TLP = TLP
        self.duration = old_duration
        self.adjusted_duration = old_duration + adjustment
        self.adjustment = adjustment
        self.acc_adjustment = acc_adjustment
        self.new_acc_adjustment = acc_adjustment + adjustment

    def force_round_up(self):
        return AdjustedDuration(
                self.TLP,
                self.duration,
                self.adjustment + 15,
                self.acc_adjustment)

    def force_round_down(self):
        return AdjustedDuration(
                self.TLP,
                self.duration,
                self.adjustment - 15,
                self.acc_adjustment)

    @property
    def _comparison_key(self):
        return self.new_acc_adjustment, self.adjusted_duration

    def __gt__(self, other):
        return self._comparison_key > other._comparison_key

    def __lt__(self, other):
        return self._comparison_key < other._comparison_key


def _best_adjustment(num_to_round, acc_adjustment):
    adjustment_up, adjustment_down = _adjustments_to_nearest_15(num_to_round)
    new_adj_up = acc_adjustment + adjustment_up
    new_adj_down = acc_adjustment + adjustment_down
    if abs(new_adj_up) < abs(new_adj_down):
        return adjustment_up
    else:
        return adjustment_down


def _adjustments_to_nearest_15(num_to_round):
    adjustment_up = _distance_up_to_the_nearest_15(num_to_round)
    adjustment_down = adjustment_up - 15 if adjustment_up != 0 else 0
    return adjustment_up, adjustment_down


def _distance_up_to_the_nearest_15(num_to_round):
    if num_to_round % 15 == 0:
        return 0
    return Sequence(range(1, 15))\
        .filter(lambda x: ((x + num_to_round) % 15) == 0)\
        .first
