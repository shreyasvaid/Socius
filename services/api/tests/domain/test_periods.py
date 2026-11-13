from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from hypothesis import given
from hypothesis import strategies as st

from socius_api.domain import (
    PeriodBounds,
    close_due_at,
    contains,
    day_start,
    first_period,
    next_period,
    overdue_at,
)
from tests.domain.strategies import days, period_lengths, zones

MICRO = timedelta(microseconds=1)


def local_date(instant: datetime, tz_name: str) -> date:
    return instant.astimezone(ZoneInfo(tz_name)).date()


def assert_is_day_start(instant: datetime, day: date, tz_name: str) -> None:
    """`instant` is the first instant of `day` in the zone."""
    assert local_date(instant, tz_name) == day
    assert local_date(instant - MICRO, tz_name) < day


# Invariant 8


@given(zone=zones, start=days, length=period_lengths)
def test_invariant_8_period_ends_at_a_day_start(zone: str, start: date, length: int) -> None:
    starts_at = day_start(start, zone)
    bounds = next_period(starts_at, zone, length)
    assert_is_day_start(bounds.ends_at, start + timedelta(days=length), zone)
    assert bounds.ends_at > bounds.starts_at


@given(old_zone=zones, new_zone=zones, start=days, length=period_lengths)
def test_invariant_8_holds_after_a_zone_change(
    old_zone: str, new_zone: str, start: date, length: int
) -> None:
    previous_end = day_start(start, old_zone)
    bounds = next_period(previous_end, new_zone, length)
    expected = local_date(previous_end, new_zone) + timedelta(days=length)
    assert_is_day_start(bounds.ends_at, expected, new_zone)
    assert bounds.ends_at > bounds.starts_at


@given(zone=zones, day=days)
def test_day_start_is_the_first_instant_of_the_day(zone: str, day: date) -> None:
    assert_is_day_start(day_start(day, zone), day, zone)


@given(
    zone=zones,
    started=st.datetimes(
        min_value=datetime(2020, 1, 1), max_value=datetime(2040, 1, 1), timezones=st.just(UTC)
    ),
    length=period_lengths,
)
def test_first_period_starts_at_the_next_day_start(
    zone: str, started: datetime, length: int
) -> None:
    bounds = first_period(started, zone, length)
    start_day = local_date(started, zone) + timedelta(days=1)
    assert bounds.starts_at > started
    assert_is_day_start(bounds.starts_at, start_day, zone)
    assert_is_day_start(bounds.ends_at, start_day + timedelta(days=length), zone)


# Invariant 9


@given(
    start=days,
    steps=st.lists(st.tuples(zones, period_lengths), min_size=1, max_size=6),
    first_zone=zones,
)
def test_invariant_9_periods_are_contiguous(
    start: date, steps: list[tuple[str, int]], first_zone: str
) -> None:
    previous_end = day_start(start, first_zone)
    for zone, length in steps:
        bounds = next_period(previous_end, zone, length)
        assert bounds.starts_at == previous_end
        previous_end = bounds.ends_at


# Examples


def hours(bounds: PeriodBounds) -> float:
    return (bounds.ends_at - bounds.starts_at) / timedelta(hours=1)


def test_seven_days_across_spring_forward_is_167_hours() -> None:
    bounds = next_period(day_start(date(2024, 3, 4), "America/Chicago"), "America/Chicago", 7)
    assert hours(bounds) == 167


def test_seven_days_across_fall_back_is_169_hours() -> None:
    bounds = next_period(day_start(date(2024, 10, 28), "America/Chicago"), "America/Chicago", 7)
    assert hours(bounds) == 169


def test_day_start_when_daylight_saving_skips_midnight() -> None:
    # Santiago: 2024-09-07 24:00 -04 jumps to 2024-09-08 01:00 -03.
    assert day_start(date(2024, 9, 8), "America/Santiago") == datetime(2024, 9, 8, 4, tzinfo=UTC)
    # Beirut: 2024-03-31 00:00 +02 jumps to 01:00 +03.
    assert day_start(date(2024, 3, 31), "Asia/Beirut") == datetime(2024, 3, 30, 22, tzinfo=UTC)


def test_day_start_when_midnight_happens_twice_is_the_earlier_one() -> None:
    # Havana: 2024-11-03 01:00 -04 falls back to 00:00 -05; midnight -04 comes first.
    assert day_start(date(2024, 11, 3), "America/Havana") == datetime(2024, 11, 3, 4, tzinfo=UTC)


def test_one_day_period_on_a_leap_day() -> None:
    bounds = next_period(day_start(date(2024, 2, 29), "UTC"), "UTC", 1)
    assert bounds.ends_at == datetime(2024, 3, 1, tzinfo=UTC)


def test_365_day_period_across_a_leap_day() -> None:
    bounds = next_period(day_start(date(2024, 1, 1), "UTC"), "UTC", 365)
    assert bounds.ends_at == datetime(2024, 12, 31, tzinfo=UTC)


def test_zone_change_between_periods() -> None:
    # Ends at midnight in New York (04:00 UTC, 13:00 in Tokyo); next is 7 days in Tokyo.
    previous_end = day_start(date(2024, 6, 10), "America/New_York")
    bounds = next_period(previous_end, "Asia/Tokyo", 7)
    assert bounds.starts_at == datetime(2024, 6, 10, 4, tzinfo=UTC)
    assert bounds.ends_at == datetime(2024, 6, 16, 15, tzinfo=UTC)  # June 17 00:00 Tokyo


def test_first_period_when_start_is_tapped_at_midnight() -> None:
    midnight = day_start(date(2024, 6, 10), "UTC")
    bounds = first_period(midnight, "UTC", 7)
    assert bounds.starts_at == datetime(2024, 6, 11, tzinfo=UTC)


def test_end_instant_is_closed_and_one_microsecond_before_is_open() -> None:
    bounds = next_period(day_start(date(2024, 6, 10), "UTC"), "UTC", 7)
    assert not contains(bounds, bounds.ends_at)
    assert contains(bounds, bounds.ends_at - MICRO)
    assert contains(bounds, bounds.starts_at)


def test_close_due_and_overdue_times() -> None:
    bounds = next_period(day_start(date(2024, 6, 10), "UTC"), "UTC", 7)
    assert close_due_at(bounds) == bounds.ends_at + timedelta(minutes=5)
    assert overdue_at(bounds) == bounds.ends_at + timedelta(minutes=60)


# Validation


@pytest.mark.parametrize("length", [0, 366, -1])
def test_period_length_outside_range_is_rejected(length: int) -> None:
    with pytest.raises(ValueError, match="period_days"):
        next_period(datetime(2024, 6, 10, tzinfo=UTC), "UTC", length)


@pytest.mark.parametrize("zone", ["Mars/Olympus", "", "../etc/passwd", "utc+5"])
def test_unknown_zone_is_rejected(zone: str) -> None:
    with pytest.raises(ValueError, match="time zone"):
        day_start(date(2024, 6, 10), zone)


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        first_period(datetime(2024, 6, 10), "UTC", 7)


def test_bounds_must_be_ordered() -> None:
    t = datetime(2024, 6, 10, tzinfo=UTC)
    with pytest.raises(ValueError, match="after"):
        PeriodBounds(t, t)
