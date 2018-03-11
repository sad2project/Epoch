from .rounding import Sequence
from epoch.cli._time_parsing import *
from typing import Callable, Tuple


__all__ = ['Time', 'TLP', 'Timestamp', 'TLPDuration', 'DurationWithAdjustment',
           'AdjustedTLPDuration']


class Time:
    def __init__(self, hour: int, minute: int):
        hour, minute = Time.fix_under_over(hour, minute)
        if hour < 0 or hour > 23 or minute < 0:
            raise AttributeError('Time cannot be negative nor the hour greater '
                                 'than 23')
        self.hour = hour
        self.minute = minute

    @classmethod
    def from_user_time(cls, user_time: str, cutoff_config: Callable[[int], bool]):
        return cls(*parse_user_time(user_time, cutoff_config))

    @classmethod
    def now(cls) -> 'Time':
        return cls(*now())

    def time_between(self, other: 'Time') -> 'Duration':
        if self < other:
            return Duration(other.hour - self.hour, other.minute - self.minute)
        else:
            return Duration(self.hour - other.hour, self.minute - other.minute)

    @property
    def components(self) -> Tuple[int, int]:
        return self.hour, self.minute

    def __str__(self) -> str:
        return f'{self.hour}:{self.minute}'

    def __eq__(self, other: 'Time') -> bool:
        return self.components == other.components

    def __lt__(self, other: 'Time') -> bool:
        return self.components < other.components

    def __gt__(self, other: 'Time') -> bool:
        return self.components > other.components

    def __ge__(self, other: 'Time') -> bool:
        return self.components >= other.components

    def __le__(self, other: 'Time') -> bool:
        return self.components <= other.components

    def __hash__(self) -> int:
        return (hash(self.hour) * 19001) ^ (hash(self.minute) * 31)

    def __add__(self, other: 'Duration') -> 'Time':
        return Time(*Time.fix_under_over(
                self.hour + other.hour,
                self.minute + other.minute))

    def __sub__(self, other: 'Duration') -> 'Time':
        return Time(*Time.fix_under_over(
                self.hour - other.hour,
                self.minute - other.minute))

    @staticmethod
    def fix_under_over(hour: int, minute: int):
        if minute < 0:
            return Time.fix_under_over(hour - 1, minute + 60)
        if minute > 60:
            return Time.fix_under_over(hour + 1, minute - 60)
        else:
            return hour, minute


class Duration:
    def __init__(self, hour: int, minute: int):
        self.modifier, hour, minute = Duration.fix_under_over(hour, minute)
        self.hour = hour
        self.minute = minute

    def is_fifteen_minute_interval(self):
        return self.minute % 15 == 0

    @property
    def components(self) -> Tuple[int, int]:
        return self.hour * self.modifier, self.minute * self.modifier

    @staticmethod
    def fix_under_over(hour: int, minute: int) -> Tuple[int, int, int]:
        new_hour, new_min = Time.fix_under_over(hour, minute)
        if new_hour < 0:
            return -1, -new_hour, new_min
        else:
            return 1, new_hour, new_min

    def __str__(self) -> str:
        opening = "" if self.modifier == 1 else "negative "
        if self.hour == 0:
            return opening + f'{self.minute} mins'
        else:
            return opening + f'{self.hour} hours {self.minute} mins'

    def __eq__(self, other: 'Duration') -> bool:
        return self.components == other.components

    def __hash__(self) -> int:
        return (hash(self.hour) * 19001) ^ (hash(self.minute) * 31)

    def __add__(self, other: 'Duration') -> 'Duration':
        s_hour, s_min = self.components
        o_hour, o_min = other.components

        return Duration(*Time.fix_under_over(
                s_hour + o_hour,
                s_min + o_min))

    def __sub__(self, other: 'Duration') -> 'Duration':
        s_hour, s_min = self.components
        o_hour, o_min = other.components

        return Duration(*Time.fix_under_over(
            s_hour - o_hour,
            s_min - o_min))

    def __abs__(self) -> 'Duration':
        return Duration(self.hour, self.minute)


# noinspection PyPep8Naming
def Minutes(minute): return Duration(0, minute)


fifteen_minutes: 'Minutes' = Minutes(15)


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
        return ((self.tlp_code, self.customer, self.product, self.code,
                self.slg, self.dlg, self.prj)
                ==
                (other.tlp_code, other.customer, other.product, other.code,
                other.slg, other.dlg, other.prj))

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


class Timestamp:
    def __init__(self, tlp: TLP, time: Time):
        self.time = time
        self.tlp = tlp

    def to(self, end_time: Time) -> 'TLPDuration':
        return TLPDuration(self.tlp, end_time.time_between(self.time))


class DurationWithAdjustment:
    def __init__(self, duration: Duration, acc_adjustment: Duration):
        self.duration = duration
        self.acc_adjustment = acc_adjustment
        self.adjustment: Duration = None

    @property
    def adjusted_duration(self) -> Duration:
        self._lazy_adjustment()
        return self.duration + self.adjustment

    @property
    def new_acc_adjustment(self) -> Duration:
        self._lazy_adjustment()
        return self.acc_adjustment + self.adjustment

    def do_best_adjustment(self) -> 'DurationWithAdjustment':
        return self

    def force_round_up(self) -> 'AdjustedDuration':
        adjustment_up, _ = _adjustments_to_nearest_15(self.duration)
        return AdjustedDuration(
                self.duration,
                adjustment_up,
                self.acc_adjustment)

    def force_round_down(self) -> 'AdjustedDuration':
        _, adjustment_down = _adjustments_to_nearest_15(self.duration)
        return AdjustedDuration(
                self.duration,
                adjustment_down,
                self.acc_adjustment)

    @property
    def _comparison_key(self):
        return self.new_acc_adjustment, self.adjusted_duration

    def _lazy_adjustment(self):
        if self.adjustment is None:
            self.adjustment = _best_adjustment(self.duration, self.acc_adjustment)

    def __gt__(self, other):
        return self._comparison_key > other._comparison_key

    def __lt__(self, other):
        return self._comparison_key < other._comparison_key


class TLPDuration:
    def __init__(self, tlp: TLP, duration: Duration):
        self.duration = duration
        self.tlp = tlp

    def has_same_tlp_as(self, other: 'TLPDuration') -> bool:
        return self.tlp == other.tlp

    def __add__(self, other: 'TLPDuration') -> 'TLPDuration':
        return TLPDuration(self.tlp + other.tlp, self.duration + other.duration)

    def __eq__(self, other) -> bool:
        return self.tlp == other.TLP

    def __hash__(self) -> int:
        return hash(self.tlp)

    def and_accumulated_adjustment(self, adjustment: int) -> DurationWithAdjustment:
        return DurationWithAdjustment(self.tlp, self.duration, adjustment)

    def with_no_accumulated_adjustment(self) -> DurationWithAdjustment:
        return DurationWithAdjustment(self.tlp, self.duration, 0)


# noinspection PyPep8Naming
class AdjustedTLPDuration:
    def __init__(self, TLP: TLP, adjusted_duration: 'AdjustedDuration'):
        self.TLP = TLP
        self.adjusted_duration = adjusted_duration

    def force_round_up(self):
        return AdjustedTLPDuration(
                self.TLP,
                self.adjusted_duration.force_round_up())

    def force_round_down(self):
        return AdjustedTLPDuration(
                self.TLP,
                self.adjusted_duration.force_round_down())

    def __gt__(self, other: 'AdjustedTLPDuration') -> bool:
        return self.adjusted_duration > other.adjusted_duration

    def __lt__(self, other: 'AdjustedTLPDuration') -> bool:
        return self.adjusted_duration < other.adjusted_duration


class AdjustedDuration:
    def __init__(self, old_duration, adjustment, acc_adjustment):
        self.duration = old_duration
        self.adjusted_duration = old_duration + adjustment
        self.adjustment = adjustment
        self.acc_adjustment = acc_adjustment
        self.new_acc_adjustment = acc_adjustment + adjustment

    def force_round_up(self):
        return AdjustedDuration(
                self.duration,
                self.adjustment + fifteen_minutes,
                self.acc_adjustment)

    def force_round_down(self):
        return AdjustedDuration(
                self.duration,
                self.adjustment - fifteen_minutes,
                self.acc_adjustment)

    @property
    def _comparison_key(self):
        return self.new_acc_adjustment, self.adjusted_duration

    def __gt__(self, other):
        return self._comparison_key > other._comparison_key

    def __lt__(self, other):
        return self._comparison_key < other._comparison_key


def _best_adjustment(num_to_round: Duration, acc_adjustment: Duration) -> Duration:
    adjustment_up, adjustment_down = _adjustments_to_nearest_15(num_to_round)
    new_adj_up = acc_adjustment + adjustment_up
    new_adj_down = acc_adjustment + adjustment_down
    if abs(new_adj_up) < abs(new_adj_down):
        return adjustment_up
    else:
        return adjustment_down


def _adjustments_to_nearest_15(num_to_round: Duration) -> Tuple[Duration, Duration]:
    adjustment_up = _distance_up_to_the_nearest_15(num_to_round)
    adjustment_down = (adjustment_up - fifteen_minutes
                       if adjustment_up.minute != Minutes(0)
                       else Minutes(0))
    return adjustment_up, adjustment_down


def _distance_up_to_the_nearest_15(num_to_round: Duration) -> Duration:
    if num_to_round.is_fifteen_minute_interval():
        return Minutes(0)
    return (Sequence(range(1, 15))
            .map(Minutes)
            .map(num_to_round.__add__)
            .filter(Duration.is_fifteen_minute_interval)
            .first)
