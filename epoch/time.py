# coding=utf-8
from typing import Tuple

from epoch.functions import Stream

__all__ = ['Time', 'Duration', 'DurationWithAdjustment', 'AdjustedDuration']


class Time:
    def __init__(self, hour: int, minute: int):
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise AttributeError('Time must a proper time of day')
        self.minutes = minute + (hour * 60)

    def time_between(self, other: 'Time') -> 'Duration':
        if self < other:
            return Duration(minutes=(other.minutes - self.minutes))
        else:
            return Duration(minutes=(self.minutes - other.minutes))

    def __str__(self) -> str:
        hour, minute = mins_to_hours_and_mins(self.minutes)
        return f'{format(hour, "0>2d")}:{format(minute, "0>2d")}'

    def __eq__(self, other: 'Time') -> bool:
        return self.minutes == other.minutes

    def __lt__(self, other: 'Time') -> bool:
        return self.minutes < other.minutes

    def __gt__(self, other: 'Time') -> bool:
        return self.minutes > other.minutes

    def __ge__(self, other: 'Time') -> bool:
        return self.minutes >= other.minutes

    def __le__(self, other: 'Time') -> bool:
        return self.minutes <= other.minutes

    def __hash__(self) -> int:
        return hash(self.minutes) * 19001

    def __add__(self, other: 'Duration') -> 'Time':
        return Time(*mins_to_hours_and_mins(self.minutes + other.minutes))

    def __sub__(self, other: 'Duration') -> 'Time':
        return Time(*mins_to_hours_and_mins(self.minutes - other.minutes))


def mins_to_hours_and_mins(mins: int) -> Tuple[int, int]:
    return mins // 60, mins % 60


class Duration:
    def __init__(self, *, hours: int=0, minutes: int):
        self.minutes = minutes + (hours * 60)

    @property
    def is_fifteen_minute_interval(self) -> bool:
        return self.minutes % 15 == 0

    def with_accumulated_adjustment(self, acc_adjustment: 'Duration') -> 'AdjustedDuration':
        return DurationWithAdjustment(self, acc_adjustment).adjust()

    def distance_to_nearest_15(
            self, acc_adjustment: 'Duration') -> 'Duration':
        adjustment_up, adjustment_down = self.adjustments_to_nearest_15s
        new_adj_up = acc_adjustment + adjustment_up
        new_adj_down = acc_adjustment + adjustment_down
        if abs(new_adj_up) < abs(new_adj_down):
            return adjustment_up
        else:
            return adjustment_down

    @property
    def adjustments_to_nearest_15s(self) -> Tuple['Duration', 'Duration']:
        if self.is_fifteen_minute_interval:
            return Duration(minutes=0), Duration(minutes=0)
        else:
            adjustment_up = self.distance_up_to_nearest_15
            adjustment_down = Duration(minutes=15) - adjustment_up
            return adjustment_up, adjustment_down

    @property
    def distance_up_to_nearest_15(self) -> 'Duration':
        if self.is_fifteen_minute_interval:
            return Duration(minutes=0)
        return (Stream(range(1, 15))
                .map(lambda x: Duration(minutes=x))
                .map(self.__add__)
                .filter(Duration.is_fifteen_minute_interval)
                .first)

    @property
    def distance_down_to_nearest_15(self):
        if self.is_fifteen_minute_interval:
            return Duration(minutes=0)
        return (Stream(range(1, 15))
                .map(lambda x: Duration(minutes=x))
                .map(self.__sub__)
                .filter(Duration.is_fifteen_minute_interval)
                .first)

    def __str__(self) -> str:
        opening = "" if self.minutes > 0 else "negative "
        if self.minutes < 60:
            return opening + f'{self.minutes} mins'
        else:
            hour, mins = mins_to_hours_and_mins(self.minutes)
            return opening + f'{hour} hours {mins} mins'

    def __eq__(self, other: 'Duration') -> bool:
        return self.minutes == other.minutes

    def __hash__(self) -> int:
        return (hash(self.minutes) * 19001)

    def __add__(self, other: 'Duration') -> 'Duration':
        return Duration(minutes=(self.minutes + other.minutes))

    def __sub__(self, other: 'Duration') -> 'Duration':
        return Duration(minutes=(self.minutes - other.minutes))

    def __abs__(self) -> 'Duration':
        return Duration(minutes=abs(self.minutes))

    def __neg__(self) -> 'Duration':
        return Duration(minutes=-self.minutes)

    def __int__(self) -> int:
        return self.minutes


class DurationWithAdjustment:
    def __init__(self, duration: Duration, acc_adjustment: Duration):
        self.duration = duration
        self.acc_adjustment = acc_adjustment
        self.adjustment: Duration = None

    def adjust(self) -> 'AdjustedDuration':
        return AdjustedDuration(
                self.duration,
                self.duration.distance_to_nearest_15(self.acc_adjustment),
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
                self.adjustment + Duration(minutes=0),
                self.acc_adjustment)

    def force_round_down(self):
        return AdjustedDuration(
                self.duration,
                self.adjustment - Duration(minutes=0),
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
