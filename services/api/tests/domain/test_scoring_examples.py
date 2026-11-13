"""Example tests: CUJs 3 and 4 with their exact numbers, and the edge cases."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from socius_api.domain import (
    MemberPeriodInput,
    MemberState,
    OutcomeKind,
    PeriodBounds,
    PeriodOutcome,
    pick_loser,
    score_period,
)

START = datetime(2024, 6, 10, tzinfo=UTC)
WEEK = PeriodBounds(START, START + timedelta(days=7))
BEFORE = START - timedelta(days=1)

P, Q, R, S = (UUID(int=i) for i in range(1, 5))


def at(day: int, hour: int = 12) -> datetime:
    return START + timedelta(days=day, hours=hour)


def member(
    user_id: UUID,
    check_ins: int = 0,
    *,
    joined_at: datetime = BEFORE,
    removed_at: datetime | None = None,
    excused: bool = False,
    extra: tuple[datetime, ...] = (),
) -> MemberPeriodInput:
    """A member with `check_ins` check-ins spread over the period, plus `extra`."""
    times = tuple(at(i % 7, 8 + i // 7) for i in range(check_ins)) + extra
    return MemberPeriodInput(user_id, joined_at, removed_at, excused, times)


def state_of(outcome: PeriodOutcome, user_id: UUID) -> MemberState:
    return next(s.state for s in outcome.scores if s.user_id == user_id)


def points_of(outcome: PeriodOutcome, user_id: UUID) -> int:
    return next(s.points for s in outcome.scores if s.user_id == user_id)


# CUJ 3: an excused member and a new joiner cannot lose


def test_cuj_3_excused_member_and_new_joiner_cannot_lose() -> None:
    outcome = score_period(
        3,
        WEEK,
        [
            member(P, 3),
            member(Q, 1),
            member(R, 0, excused=True),
            member(S, joined_at=at(2), extra=(at(3), at(4))),
        ],
    )
    assert outcome.kind is OutcomeKind.SINGLE_LOSER
    assert outcome.candidates == (Q,)
    assert state_of(outcome, R) is MemberState.EXCUSED
    assert state_of(outcome, S) is MemberState.JOINED_MID_PERIOD
    assert points_of(outcome, S) == 2


def test_cuj_3_with_q_also_excused_there_is_no_loser() -> None:
    outcome = score_period(
        3,
        WEEK,
        [
            member(P, 3),
            member(Q, 1, excused=True),
            member(R, 0, excused=True),
            member(S, joined_at=at(2), extra=(at(3), at(4))),
        ],
    )
    assert outcome.kind is OutcomeKind.NO_LOSER_TOO_FEW_ELIGIBLE
    assert outcome.candidates == ()


# CUJ 4: two check-ins in one day


def test_cuj_4_two_check_ins_in_one_day_reach_n_and_more_are_capped() -> None:
    morning, evening = at(3, 7), at(3, 19)
    jordan = member(P, 2, extra=(morning, evening))
    assert points_of(score_period(4, WEEK, [jordan, member(Q, 4)]), P) == 4

    fifth = member(P, 2, extra=(morning, evening, at(4)))
    outcome = score_period(4, WEEK, [fifth, member(Q, 4)])
    score = next(s for s in outcome.scores if s.user_id == P)
    assert (score.points, score.counted_check_ins) == (4, 5)


# Small groups


def test_solo_group_has_no_loser() -> None:
    outcome = score_period(3, WEEK, [member(P, 0)])
    assert outcome.kind is OutcomeKind.NO_LOSER_TOO_FEW_ELIGIBLE


def test_couple_with_one_excused_has_no_loser() -> None:
    outcome = score_period(3, WEEK, [member(P, 0), member(Q, 0, excused=True)])
    assert outcome.kind is OutcomeKind.NO_LOSER_TOO_FEW_ELIGIBLE


def test_everyone_reaching_n_means_no_loser() -> None:
    outcome = score_period(2, WEEK, [member(P, 2), member(Q, 5)])
    assert outcome.kind is OutcomeKind.NO_LOSER_ALL_REACHED_TARGET


# Ties


def test_everyone_at_zero_needs_a_tiebreak_among_everyone() -> None:
    outcome = score_period(3, WEEK, [member(S), member(P), member(R), member(Q)])
    assert outcome.kind is OutcomeKind.TIEBREAK_NEEDED
    assert outcome.candidates == (P, Q, R, S)


def test_pick_loser_sorts_before_choosing() -> None:
    first = lambda seq: seq[0]  # noqa: E731
    assert pick_loser([S, Q, P], first) == P


def test_pick_loser_needs_a_candidate() -> None:
    with pytest.raises(ValueError, match="no candidates"):
        pick_loser([])


# Joiners and removals


def test_joiner_check_ins_before_joining_are_ignored() -> None:
    joiner = member(S, joined_at=at(3), extra=(at(1), at(2), at(4)))
    outcome = score_period(3, WEEK, [member(P, 3), member(Q, 3), joiner])
    assert points_of(outcome, S) == 1


def test_removed_member_is_excused_and_keeps_points_up_to_removal() -> None:
    removed = member(R, removed_at=at(3), extra=(at(1), at(2), at(4)))
    outcome = score_period(3, WEEK, [member(P, 3), member(Q, 1), removed])
    assert state_of(outcome, R) is MemberState.EXCUSED
    assert points_of(outcome, R) == 2
    assert outcome.candidates == (Q,)


def test_re_added_member_is_eligible_again() -> None:
    # Re-adding in the same period clears removed_at on the same membership.
    readded = member(R, 0)
    outcome = score_period(3, WEEK, [member(P, 3), member(Q, 1), readded])
    assert state_of(outcome, R) is MemberState.ELIGIBLE
    assert outcome.candidates == (R,)


def test_member_removed_after_the_period_ended_can_lose() -> None:
    late = member(R, 0, removed_at=WEEK.ends_at + timedelta(hours=1))
    outcome = score_period(3, WEEK, [member(P, 3), late])
    assert state_of(outcome, R) is MemberState.ELIGIBLE
    assert outcome.candidates == (R,)


def test_check_in_at_the_end_instant_counts_in_the_next_period() -> None:
    outcome = score_period(3, WEEK, [member(P, extra=(WEEK.ends_at,)), member(Q, 1)])
    assert points_of(outcome, P) == 0


# Cap


def test_n_of_one_caps_ten_check_ins_at_one() -> None:
    outcome = score_period(1, WEEK, [member(P, 10), member(Q, 0)])
    assert points_of(outcome, P) == 1
    assert outcome.candidates == (Q,)


# Validation


@pytest.mark.parametrize("target_n", [0, 101])
def test_target_outside_range_is_rejected(target_n: int) -> None:
    with pytest.raises(ValueError, match="target_n"):
        score_period(target_n, WEEK, [member(P)])


def test_duplicate_user_is_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        score_period(3, WEEK, [member(P), member(P)])


@pytest.mark.parametrize(
    "outsider",
    [
        member(P, joined_at=WEEK.ends_at),  # joined after the period
        member(P, removed_at=START - timedelta(seconds=1)),  # removed before it started
    ],
)
def test_member_outside_the_member_set_is_rejected(outsider: MemberPeriodInput) -> None:
    with pytest.raises(ValueError, match="member set"):
        score_period(3, WEEK, [outsider])
