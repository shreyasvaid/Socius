"""Hypothesis strategies for the domain tests."""

from datetime import date, datetime, timedelta
from uuid import UUID

from hypothesis import strategies as st

from socius_api.domain import MemberPeriodInput, PeriodBounds, day_start, in_member_set

# With and without daylight saving, half-hour and 45-minute offsets, the extremes,
# and zones where daylight saving skips midnight (Santiago, Havana, Beirut).
ZONES = (
    "UTC",
    "America/Chicago",
    "America/New_York",
    "America/Los_Angeles",
    "Europe/London",
    "Europe/Berlin",
    "Asia/Kolkata",
    "Asia/Kathmandu",
    "Australia/Adelaide",
    "Australia/Lord_Howe",
    "Asia/Tokyo",
    "Pacific/Kiritimati",
    "Etc/GMT+12",
    "America/Santiago",
    "America/Havana",
    "Asia/Beirut",
)

zones = st.sampled_from(ZONES)
days = st.dates(min_value=date(2020, 1, 1), max_value=date(2040, 12, 31))
period_lengths = st.integers(min_value=1, max_value=365)
# Small targets make "everyone reached N" and ties common; the full range still appears.
targets = st.one_of(st.integers(min_value=1, max_value=5), st.integers(min_value=1, max_value=100))

# Microsecond offsets let draws hit exact boundaries and their neighbours.
_MICRO = timedelta(microseconds=1)


@st.composite
def instants(draw: st.DrawFn, lo: datetime, hi: datetime) -> datetime:
    """Any instant in [lo, hi], biased towards the ends and their neighbours."""
    span = int((hi - lo) / _MICRO)
    offset = draw(
        st.one_of(
            st.integers(0, span),
            st.sampled_from([0, 1, span - 1, span]).filter(lambda x: 0 <= x <= span),
        )
    )
    return lo + offset * _MICRO


@st.composite
def period_bounds(draw: st.DrawFn) -> PeriodBounds:
    zone = draw(zones)
    start = draw(days)
    length = draw(st.integers(min_value=1, max_value=30))  # keeps check-in density useful
    return PeriodBounds(day_start(start, zone), day_start(start + timedelta(days=length), zone))


@st.composite
def members(draw: st.DrawFn, bounds: PeriodBounds) -> MemberPeriodInput:
    """A membership in the period's member set, with check-ins in and around it."""
    margin = timedelta(days=2)
    # Most members play the whole period, so eligible groups and real losers are common.
    if draw(_one_in(5)):
        joined_at = draw(instants(bounds.starts_at, bounds.ends_at - _MICRO))  # joined mid-period
    else:
        joined_at = draw(instants(bounds.starts_at - margin, bounds.starts_at))
    removed_at = None
    if draw(_one_in(5)):
        removed_at = draw(instants(max(joined_at, bounds.starts_at), bounds.ends_at + margin))
    assert in_member_set(joined_at, removed_at, bounds)
    inside = instants(bounds.starts_at, bounds.ends_at - _MICRO)
    around = instants(bounds.starts_at - margin, bounds.ends_at + margin)
    check_ins = draw(st.lists(st.one_of(inside, inside, around), max_size=15))
    return MemberPeriodInput(
        user_id=draw(st.uuids()),
        joined_at=joined_at,
        removed_at=removed_at,
        excused=draw(_one_in(5)),
        check_in_times=tuple(check_ins),
    )


def _one_in(n: int) -> st.SearchStrategy[bool]:
    return st.integers(min_value=1, max_value=n).map(lambda x: x == 1)


@st.composite
def periods(draw: st.DrawFn) -> tuple[int, PeriodBounds, list[MemberPeriodInput]]:
    """A target, bounds and a member set of 1-12 (up to 8 active plus removed ones)."""
    bounds = draw(period_bounds())
    member_list = draw(
        st.lists(members(bounds), min_size=1, max_size=12, unique_by=lambda m: m.user_id)
    )
    return draw(targets), bounds, member_list


def by_id(member_list: list[MemberPeriodInput]) -> dict[UUID, MemberPeriodInput]:
    return {m.user_id: m for m in member_list}
