"""Period arithmetic in a group's time zone.

Pure functions: no I/O and no clock. Every datetime in and out is timezone-aware;
outputs are in UTC. See the engine design, "Time model".
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MIN_PERIOD_DAYS = 1
MAX_PERIOD_DAYS = 365
CLOSE_DELAY = timedelta(minutes=5)
OVERDUE_AFTER = timedelta(minutes=60)


@dataclass(frozen=True, slots=True)
class PeriodBounds:
    """A half-open interval [starts_at, ends_at) in UTC."""

    starts_at: datetime
    ends_at: datetime

    def __post_init__(self) -> None:
        _require_aware(self.starts_at, "starts_at")
        _require_aware(self.ends_at, "ends_at")
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")


def day_start(day: date, tz_name: str) -> datetime:
    """The first instant of `day` in the zone, as UTC.

    That is local midnight, or, where daylight saving skips midnight, the moment
    the clocks jump (for example 01:00 in America/Santiago).
    """
    zone = _zone(tz_name)
    midnight = datetime.combine(day, time(0), tzinfo=zone)
    # fold=0 picks the earlier instant when midnight happens twice.
    candidate = midnight.astimezone(UTC)
    if candidate.astimezone(zone).replace(tzinfo=None) == midnight.replace(tzinfo=None):
        return candidate
    return _first_instant_in_gap(day, midnight, zone)


def first_period(started_at: datetime, tz_name: str, period_days: int) -> PeriodBounds:
    """The first period after the admin taps Start: it begins at the next day start."""
    _require_aware(started_at, "started_at")
    _validate_period_days(period_days)
    start_day = _local_date(started_at, tz_name) + timedelta(days=1)
    return PeriodBounds(
        starts_at=day_start(start_day, tz_name),
        ends_at=day_start(start_day + timedelta(days=period_days), tz_name),
    )


def next_period(previous_ends_at: datetime, tz_name: str, period_days: int) -> PeriodBounds:
    """The period that starts when the previous one ends.

    The end is `period_days` local days after the start's local date in `tz_name`.
    If the zone changed, the start isn't a day start in the new zone, so this one
    period is a few hours shorter or longer than its set length.
    """
    _require_aware(previous_ends_at, "previous_ends_at")
    _validate_period_days(period_days)
    start_day = _local_date(previous_ends_at, tz_name)
    return PeriodBounds(
        starts_at=previous_ends_at.astimezone(UTC),
        ends_at=day_start(start_day + timedelta(days=period_days), tz_name),
    )


def contains(bounds: PeriodBounds, instant: datetime) -> bool:
    """Whether `instant` falls in the period. The end instant belongs to the next one."""
    _require_aware(instant, "instant")
    return bounds.starts_at <= instant < bounds.ends_at


def close_due_at(bounds: PeriodBounds) -> datetime:
    """When the close may run: late writes have had time to commit or fail."""
    return bounds.ends_at + CLOSE_DELAY


def overdue_at(bounds: PeriodBounds) -> datetime:
    """When an unclosed period counts as overdue for monitoring."""
    return bounds.ends_at + OVERDUE_AFTER


def validate_zone(tz_name: str) -> None:
    """Raise ValueError unless `tz_name` is a known IANA zone."""
    _zone(tz_name)


def _zone(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"unknown time zone: {tz_name!r}") from exc


def _local_date(instant: datetime, tz_name: str) -> date:
    return instant.astimezone(_zone(tz_name)).date()


def _validate_period_days(period_days: int) -> None:
    if not MIN_PERIOD_DAYS <= period_days <= MAX_PERIOD_DAYS:
        raise ValueError(
            f"period_days must be {MIN_PERIOD_DAYS}-{MAX_PERIOD_DAYS}, got {period_days}"
        )


def _require_aware(value: datetime, name: str) -> None:
    if value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def _first_instant_in_gap(day: date, midnight: datetime, zone: ZoneInfo) -> datetime:
    """Midnight doesn't exist: find the transition instant by bisection.

    In a gap, fold=1 maps the wall time with the offset after the transition (an
    instant before it) and fold=0 with the offset before it (an instant after it),
    so the transition lies between the two. Transitions fall on whole seconds.
    """
    lo = midnight.replace(fold=1).astimezone(UTC)  # local date is the day before
    hi = midnight.replace(fold=0).astimezone(UTC)  # local date is `day`
    step = timedelta(seconds=1)
    while hi - lo > step:
        mid = lo + (hi - lo) // 2
        mid = mid.replace(microsecond=0)
        if mid.astimezone(zone).date() >= day:
            hi = mid
        else:
            lo = mid
    return hi
