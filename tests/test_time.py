import pytest
from hamcrest import *

from epoch.cli._time_parsing import _standardize_ampm, from_user_time, now
from epoch.time import *


def cutoff_time(hour):
    def is_afternoon(input):
        return input < hour
    return is_afternoon


@pytest.fixture(params=("+0", "+1", "-1", "+22", "-45", "+55"))
def relative(request):
    return request.param


def test_relative_time(relative):
    relative_dur = Minutes(int(relative))
    expected = Time(*now()) + relative_dur

    result = from_user_time(relative, cutoff_time(7))

    assert_that(result, equal_to(expected))


def test_24_hour():
    time_text = "14:34"
    result = from_user_time(time_text, cutoff_time(7))

    assert_that(result, equal_to(Time(14, 34)))


def test_cutoff_after():
    time_text = "7:15"
    result = from_user_time(time_text, cutoff_time(7))

    assert_that(result, equal_to(Time(7, 15)))


def test_cutoff_before():
    time_text = "6:59"
    result = from_user_time(time_text, cutoff_time(7))

    assert_that(result, equal_to(Time(18, 59)))


def test_rejects_bad_time1():
    time_text = "24:10"
    try:
        result = from_user_time(time_text, cutoff_time(7))
        raise AssertionError("Expected to see a ValueError that the time is invalid")
    except ValueError:
        pass


def test_rejects_bad_time2():
    time_text = "12:62"
    try:
        result = from_user_time(time_text, cutoff_time(7))
        raise AssertionError(f"Expected to see a ValueError that the time is invalid, but got {result}")
    except ValueError:
        pass


def test_rejects_bad_ampm1():
    time_text = "13:30AM"
    try:
        result = from_user_time(time_text, cutoff_time(7))
        raise AssertionError(f"Expected to see a ValueError that the time is invalid, but got {result}")
    except ValueError:
        pass


def test_rejects_bad_ampm2():
    time_text = "12:70AM"
    try:
        result = from_user_time(time_text, cutoff_time(7))
        raise AssertionError(f"Expected to see a ValueError that the time is invalid, but got {result}")
    except ValueError:
        pass


def test_rejects_bad_ampm3():
    time_text = "13:30AM"
    try:
        result = from_user_time(time_text, cutoff_time(7))
        raise AssertionError(f"Expected to see a ValueError that the time is invalid, but got {result}")
    except ValueError:
        pass


def test_dot_separator():
    time_text = "12.10"
    result = from_user_time(time_text, cutoff_time(7))

    assert_that(result, equal_to(Time(12, 10)))


def test_semicolon_separator():
    time_text = "4;15"
    result = from_user_time(time_text, cutoff_time(7))

    assert_that(result, equal_to(Time(16, 15)))


@pytest.fixture(params=("a", "am", "A", "AM", "aM", "Am"))
def AM(request):
    return request.param


def test_am(AM):
    result = _standardize_ampm(AM)

    assert_that(result, equal_to('A'))


@pytest.fixture(params=("p", "pm", "P", "PM", "pM", "Pm"))
def PM(request):
    return request.param


def test_pm(PM):
    result = _standardize_ampm(PM)

    assert_that(result, equal_to('P'))


@pytest.fixture(params=("ap", "AP", "aPM", "M", "Pma", "g", "gm", "mp", "ma"))
def bad_ampm(request):
    return request.param


def test_bad_ampm(bad_ampm):
    try:
        _standardize_ampm(bad_ampm)
        raise AssertionError(f"Expected '{bad_ampm}' to raise a ValueError")
    except ValueError:
        pass
