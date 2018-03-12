from typing import Callable, Tuple
from datetime import datetime
from epoch.time_types import Time


__all__ = ['parse_user_time', 'now']


def now():
    now_time: Tuple[int, int] = datetime.now().time()
    return Time(*now_time)


def from_user_time(user_time: str, cutoff_config: Callable[[int], bool]):
    return Time(*parse_user_time(user_time, cutoff_config))


Time.now = staticmethod(now)
Time.from_user_time = staticmethod(from_user_time)


separator_characters = ['.', ';', ':']


def parse_user_time(user_time, pm_cutoff):
    if user_time == "":
        return now()
    elif user_time.startswith('+') or user_time.startswith('-'):
        return _parse_relative_time(user_time)
    else:
        return _parse_absolute_time(user_time, pm_cutoff)


def _parse_relative_time(user_time):
    minute_adjustment = int(user_time)
    now_hour, now_minute = now()
    return Time.fix_under_over(now_hour, now_minute + minute_adjustment)


def _parse_absolute_time(user_time, cutoff_config):
    for separator in separator_characters:
        if separator in user_time:
            return _parse_absolute_time_with_separator(
                    user_time,
                    separator,
                    cutoff_config)
    else:
        raise ValueError("""User time stamp was improperly formatted.
        enter help --time for help with the time formatting""")


def _parse_absolute_time_with_separator(user_time, separator, is_afternoon):
    hour_str, rest = user_time.split(separator)
    int_hour = int(hour_str)
    if rest.isnumeric():
        return _parse_no_ampm(int_hour, int(rest), is_afternoon)
    else:
        return _parse_with_ampm(int_hour, int(rest[:2]), rest[2:].strip())


def _parse_no_ampm(hour, minute, is_afternoon):
    return _verify_no_ampm_hour(hour, is_afternoon), _verify_minute(minute)


def _verify_no_ampm_hour(hour, is_afternoon):
    if hour < 12 and is_afternoon(hour):
        return hour + 12
    elif 0 <= hour < 24:
        return hour
    else:
        raise ValueError(f"Invalid hour amount, {hour}. Must be between 0 "
                         "(inclusively) and 24 (exclusively)")


def _verify_minute(minute):
    if 0 <= minute < 60:
        return minute
    else:
        raise ValueError(f"Invalid minute amount, {minute}. Must be between 0 "
                         "(inclusively) and 60 (exclusively)")


def _parse_with_ampm(hour, minute, ampm):
    return ((_parse_ampm_hour(hour) +
            _adjustment_for_pm(_standardize_ampm(ampm))),
            _verify_minute(minute))


def _parse_ampm_hour(hour):
    if 0 < hour <= 12:
        return hour
    else:
        raise ValueError(f"Invalid hour amount, {hour}. Must be between 0 "
                         "(inclusively) and 24 (exclusively)")


# noinspection PyPep8Naming
def _standardize_ampm(ampm):
    AMPM = ampm.upper()
    if len(AMPM) > 2:
        raise ValueError(f'"{ampm}" is an invalid AM/PM indicator')
    elif not AMPM.startswith('A') and not AMPM.startswith('P'):
        raise ValueError(f'"{ampm}" is an invalid AM/PM indicator')
    elif len(AMPM) == 2 and 'M' not in AMPM:
        raise ValueError(f'"{ampm}" is an invalid AM/PM indicator')
    return AMPM[0]


def _adjustment_for_pm(ampm):
    return 12 if _is_pm(ampm) else 0


def _is_pm(ampm):
    return 'P' == ampm
