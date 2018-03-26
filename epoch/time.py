# coding=utf-8
from typing import Tuple

from .rounding import Sequence

__all__ = ['Time', 'Minutes', 'fifteen_minutes', 'Duration', 'DurationWithAdjustment', 'AdjustedDuration']


class Time:
    def __init__(self, hour: int, minute: int):
        hour, minute = Time.fix_under_over(hour, minute)
        if hour < 0 or hour > 23 or minute < 0:
            raise AttributeError('Time cannot be negative nor the hour greater '
                                 'than 23')
        self.hour = hour
        self.minute = minute

    def time_between(self, other: 'Time') -> 'Duration':
        if self < other:
            return Duration(other.hour - self.hour, other.minute - self.minute)
        else:
            return Duration(self.hour - other.hour, self.minute - other.minute)

    @property
    def _components(self) -> Tuple[int, int]:
        return self.hour, self.minute

    def __str__(self) -> str:
        return f'{self.hour}:{self.minute}'

    def __eq__(self, other: 'Time') -> bool:
        return self._components == other._components

    def __lt__(self, other: 'Time') -> bool:
        return self._components < other._components

    def __gt__(self, other: 'Time') -> bool:
        return self._components > other._components

    def __ge__(self, other: 'Time') -> bool:
        return self._components >= other._components

    def __le__(self, other: 'Time') -> bool:
        return self._components <= other._components

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


# noinspection PyPep8Naming
def Minutes(minute): return Duration(0, minute)


fifteen_minutes: 'Minutes' = Minutes(15)


class Duration:
    def __init__(self, hour: int, minute: int):
        self.modifier, self.hour, self.minute = Duration._fix_under_over(hour, minute)

    @property
    def is_fifteen_minute_interval(self) -> bool:
        return self.minute % 15 == 0

    @property
    def _components(self) -> Tuple[int, int]:
        return self.hour * self.modifier, self.minute * self.modifier

    @staticmethod
    def _fix_under_over(hour: int, minute: int) -> Tuple[int, int, int]:
        if minute <= -60:
            return Duration._fix_under_over(hour-1, minute+60)
        elif minute >= 60:
            return Duration._fix_under_over(hour+1, minute-60)
        else:
            return Duration._calc_time_parts(hour, minute)

    @staticmethod
    def _calc_time_parts(hour: int, minute: int) -> Tuple[int, int, int]:
        if minute < 0 and hour > 0:
            return 1, hour-1, minute+60
        elif minute > 0 and hour < 0:
            return -1, hour+1, minute-60
        elif minute == 0 and hour == 0:
            return 1, 0, 0
        elif minute <= 0 and hour <= 0:
            return -1, -hour, -minute
        else:
            return 1, hour, minute

    def with_accumulated_adjustment(self, acc_adjustment):
        return DurationWithAdjustment(self, acc_adjustment)

    def distance_to_nearest_15(
            self, acc_adjustment: 'Duration'=Minutes(0)) -> 'Duration':
        adjustment_up, adjustment_down = self.adjustments_to_nearest_15s
        new_adj_up = acc_adjustment + adjustment_up
        new_adj_down = acc_adjustment + adjustment_down
        if abs(new_adj_up) < abs(new_adj_down):
            return adjustment_up
        else:
            return adjustment_down

    @property
    def adjustments_to_nearest_15s(self) -> Tuple['Duration', 'Duration']:
        adjustment_up = self.distance_up_to_nearest_15
        adjustment_down = (adjustment_up - fifteen_minutes
                           if adjustment_up.minute != Minutes(0)
                           else Minutes(0))
        return adjustment_up, adjustment_down

    @property
    def distance_up_to_nearest_15(self) -> 'Duration':
        if self.is_fifteen_minute_interval:
            return Minutes(0)
        return (Sequence(range(1, 15))
                .map(Minutes)
                .map(self.__add__)
                .filter(Duration.is_fifteen_minute_interval)
                .first)

    @property
    def distance_down_to_nearest_15(self):
        if self.is_fifteen_minute_interval:
            return Minutes(0)
        return (Sequence(range(1, 15))
                .map(Minutes)
                .map(self.__sub__)
                .filter(Duration.is_fifteen_minute_interval)
                .first)

    def __str__(self) -> str:
        opening = "" if self.modifier == 1 else "negative "
        if self.hour == 0:
            return opening + f'{self.minute} mins'
        else:
            return opening + f'{self.hour} hours {self.minute} mins'

    def __eq__(self, other: 'Duration') -> bool:
        return self._components == other._components

    def __hash__(self) -> int:
        return (hash(self.hour) * 19001) ^ (hash(self.minute) * 31)

    def __add__(self, other: 'Duration') -> 'Duration':
        s_hour, s_min = self._components
        o_hour, o_min = other._components

        return Duration(*Time.fix_under_over(
                s_hour + o_hour,
                s_min + o_min))

    def __sub__(self, other: 'Duration') -> 'Duration':
        s_hour, s_min = self._components
        o_hour, o_min = other._components

        return Duration(*Time.fix_under_over(
            s_hour - o_hour,
            s_min - o_min))

    def __abs__(self) -> 'Duration':
        return Duration(self.hour, self.minute)

    def __neg__(self) -> 'Duration':
        return Duration(*self._components)


class DurationWithAdjustment:
    def __init__(self, duration: Duration, acc_adjustment: Duration):
        self.duration = duration
        self.acc_adjustment = acc_adjustment
        self.adjustment: Duration = None

    def with_best_adjustment(self) -> 'AdjustedDuration':
        return AdjustedDuration(
                self.duration,
                self.duration.distance_to_nearest_15(self.acc_adjustment),
                self.acc_adjustment)

    def force_round_up(self) -> 'AdjustedDuration':
        return AdjustedDuration(
                self.duration,
                self.duration.distance_up_to_nearest_15,
                self.acc_adjustment)

    def force_round_down(self) -> 'AdjustedDuration':
        return AdjustedDuration(
                self.duration,
                self.duration.distance_down_to_nearest_15,
                self.acc_adjustment)


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

    def __gt__(self, other: 'AdjustedDuration'):
        return self._comparison_key > other._comparison_key

    def __lt__(self, other: 'AdjustedDuration'):
        return self._comparison_key < other._comparison_key


def _best_adjustment(
        num_to_round: Duration, acc_adjustment: Duration) -> Duration:
    adjustment_up, adjustment_down = num_to_round.adjustments_to_nearest_15s
    new_adj_up = acc_adjustment + adjustment_up
    new_adj_down = acc_adjustment + adjustment_down
    if abs(new_adj_up) < abs(new_adj_down):
        return adjustment_up
    else:
        return adjustment_down



