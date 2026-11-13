"""Property tests for invariants 1-7 and the pure part of invariant 12."""

import dataclasses
import secrets
import uuid
from datetime import datetime, timedelta
from uuid import UUID

import pytest
from hypothesis import given
from hypothesis import strategies as st

from socius_api.domain import (
    MemberPeriodInput,
    MemberState,
    PeriodBounds,
    PeriodOutcome,
    pick_loser,
    score_period,
)
from tests.domain.strategies import instants, periods

Period = tuple[int, PeriodBounds, list[MemberPeriodInput]]


def score_of(outcome: PeriodOutcome, user_id: UUID) -> int:
    return next(s.points for s in outcome.scores if s.user_id == user_id)


def with_check_in(member: MemberPeriodInput, t: datetime) -> MemberPeriodInput:
    return dataclasses.replace(member, check_in_times=(*member.check_in_times, t))


@given(periods())
def test_invariant_1_points_are_between_zero_and_n(period: Period) -> None:
    target_n, bounds, members = period
    outcome = score_period(target_n, bounds, members)
    assert all(0 <= s.points <= target_n for s in outcome.scores)


@given(period=periods(), data=st.data())
def test_invariant_2_a_check_in_never_lowers_points_or_makes_a_candidate(
    period: Period, data: st.DataObject
) -> None:
    target_n, bounds, members = period
    i = data.draw(st.integers(0, len(members) - 1))
    t = data.draw(instants(bounds.starts_at - timedelta(days=1), bounds.ends_at))
    member = members[i]
    after = [*members[:i], with_check_in(member, t), *members[i + 1 :]]

    before_outcome = score_period(target_n, bounds, members)
    after_outcome = score_period(target_n, bounds, after)

    assert score_of(after_outcome, member.user_id) >= score_of(before_outcome, member.user_id)
    if member.user_id not in before_outcome.candidates:
        assert member.user_id not in after_outcome.candidates


@given(periods())
def test_invariant_3_no_loser_iff_too_few_eligible_or_all_reached_n(period: Period) -> None:
    target_n, bounds, members = period
    outcome = score_period(target_n, bounds, members)
    eligible = [s for s in outcome.scores if s.state is MemberState.ELIGIBLE]
    no_loser = len(eligible) < 2 or all(s.points == target_n for s in eligible)
    assert (outcome.candidates == ()) == no_loser


@given(periods())
def test_invariant_4_the_loser_is_eligible_and_has_the_lowest_points(period: Period) -> None:
    target_n, bounds, members = period
    outcome = score_period(target_n, bounds, members)
    if not outcome.candidates:
        return
    eligible = [s for s in outcome.scores if s.state is MemberState.ELIGIBLE]
    lowest = min(s.points for s in eligible)
    assert set(outcome.candidates) == {s.user_id for s in eligible if s.points == lowest}
    assert pick_loser(outcome.candidates) in outcome.candidates


@given(period=periods(), data=st.data())
def test_invariant_5_non_eligible_check_ins_never_change_candidates(
    period: Period, data: st.DataObject
) -> None:
    target_n, bounds, members = period
    before = score_period(target_n, bounds, members)
    states = {s.user_id: s.state for s in before.scores}
    window = instants(bounds.starts_at - timedelta(days=1), bounds.ends_at + timedelta(days=1))
    changed = [
        m
        if states[m.user_id] is MemberState.ELIGIBLE
        else dataclasses.replace(m, check_in_times=tuple(data.draw(st.lists(window, max_size=15))))
        for m in members
    ]
    assert score_period(target_n, bounds, changed).candidates == before.candidates


@given(period=periods(), data=st.data())
def test_invariant_6_input_order_does_not_matter(period: Period, data: st.DataObject) -> None:
    target_n, bounds, members = period
    shuffled = data.draw(st.permutations(members))
    assert score_period(target_n, bounds, shuffled) == score_period(target_n, bounds, members)


@given(period=periods(), data=st.data())
def test_invariant_7_check_ins_outside_membership_never_change_points(
    period: Period, data: st.DataObject
) -> None:
    target_n, bounds, members = period
    i = data.draw(st.integers(0, len(members) - 1))
    member = members[i]
    lo, hi = bounds.starts_at - timedelta(days=3), bounds.ends_at + timedelta(days=3)
    outside = [
        instants(lo, bounds.starts_at - timedelta(microseconds=1)),
        instants(bounds.ends_at, hi),
    ]
    if member.joined_at > lo:
        outside.append(instants(lo, member.joined_at - timedelta(microseconds=1)))
    if member.removed_at is not None:
        outside.append(instants(member.removed_at, max(member.removed_at, hi)))
    t = data.draw(st.one_of(outside))
    after = [*members[:i], with_check_in(member, t), *members[i + 1 :]]

    before_points = score_of(score_period(target_n, bounds, members), member.user_id)
    after_points = score_of(score_period(target_n, bounds, after), member.user_id)
    assert after_points == before_points


@given(periods())
def test_invariant_12_a_member_removed_during_the_period_is_never_a_candidate(
    period: Period,
) -> None:
    target_n, bounds, members = period
    outcome = score_period(target_n, bounds, members)
    for m in members:
        if m.removed_at is not None and m.removed_at < bounds.ends_at:
            assert m.user_id not in outcome.candidates
            state = next(s.state for s in outcome.scores if s.user_id == m.user_id)
            assert state is not MemberState.ELIGIBLE


@given(st.lists(st.uuids(), min_size=1, max_size=8, unique=True))
def test_pick_loser_returns_a_candidate(candidates: list[UUID]) -> None:
    assert pick_loser(candidates) in candidates


@pytest.mark.parametrize("size", range(2, 9))
def test_pick_loser_can_pick_every_candidate(size: int) -> None:
    # With 8 candidates, missing one in 1,000 draws has probability below 1e-56.
    candidates = [uuid.uuid4() for _ in range(size)]
    picked = {pick_loser(candidates, secrets.choice) for _ in range(1000)}
    assert picked == set(candidates)
