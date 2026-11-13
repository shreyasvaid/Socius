"""Eligibility, points and the loser rule for one period.

Pure functions: the caller loads the member set, excusals and check-ins and passes
them in. See the engine design, "Eligibility and the loser rule".
"""

import secrets
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from socius_api.domain.periods import PeriodBounds, contains

SCORING_VERSION = 1
MIN_TARGET_N = 1
MAX_TARGET_N = 100


class MemberState(StrEnum):
    ELIGIBLE = "eligible"
    JOINED_MID_PERIOD = "joined_mid_period"
    EXCUSED = "excused"


class OutcomeKind(StrEnum):
    NO_LOSER_TOO_FEW_ELIGIBLE = "no_loser_too_few_eligible"
    NO_LOSER_ALL_REACHED_TARGET = "no_loser_all_reached_target"
    SINGLE_LOSER = "single_loser"
    TIEBREAK_NEEDED = "tiebreak_needed"


@dataclass(frozen=True, slots=True)
class MemberPeriodInput:
    user_id: UUID
    joined_at: datetime
    removed_at: datetime | None
    excused: bool
    """An active excusal exists for the period. Removal is read from `removed_at`."""
    check_in_times: tuple[datetime, ...]
    """Active (not undone) check-ins. Ones outside the period are ignored."""


@dataclass(frozen=True, slots=True)
class MemberScore:
    user_id: UUID
    state: MemberState
    counted_check_ins: int
    points: int


@dataclass(frozen=True, slots=True)
class PeriodOutcome:
    scores: tuple[MemberScore, ...]
    """Sorted by user ID."""
    candidates: tuple[UUID, ...]
    """Members who could lose, sorted by user ID. Empty when there is no loser."""
    kind: OutcomeKind


def in_member_set(joined_at: datetime, removed_at: datetime | None, bounds: PeriodBounds) -> bool:
    """Whether a membership belongs to the period's member set."""
    return joined_at < bounds.ends_at and (removed_at is None or removed_at >= bounds.starts_at)


def member_state(
    joined_at: datetime, removed_at: datetime | None, excused: bool, bounds: PeriodBounds
) -> MemberState:
    """Joining mid-period takes precedence over an excusal or a removal.

    All three non-eligible reasons mean "can't lose"; the order only picks the label.
    """
    if joined_at > bounds.starts_at:
        return MemberState.JOINED_MID_PERIOD
    removed_during_period = removed_at is not None and removed_at < bounds.ends_at
    if excused or removed_during_period:
        return MemberState.EXCUSED
    return MemberState.ELIGIBLE


def counted_check_ins(member: MemberPeriodInput, bounds: PeriodBounds) -> int:
    """Check-ins inside the period made while the member belonged to the group."""
    return sum(1 for t in member.check_in_times if _counts(member, bounds, t))


def points(member: MemberPeriodInput, target_n: int, bounds: PeriodBounds) -> int:
    return min(target_n, counted_check_ins(member, bounds))


def score_period(
    target_n: int, bounds: PeriodBounds, members: Sequence[MemberPeriodInput]
) -> PeriodOutcome:
    """Score every member and find the loser candidates.

    Raises ValueError for a target outside 1-100, a duplicate user, or a member
    who isn't in the period's member set.
    """
    _validate(target_n, bounds, members)

    scores = tuple(
        _score(member, target_n, bounds) for member in sorted(members, key=lambda m: m.user_id)
    )
    eligible = [s for s in scores if s.state is MemberState.ELIGIBLE]

    if len(eligible) < 2:
        return PeriodOutcome(scores, (), OutcomeKind.NO_LOSER_TOO_FEW_ELIGIBLE)
    if all(s.points == target_n for s in eligible):
        return PeriodOutcome(scores, (), OutcomeKind.NO_LOSER_ALL_REACHED_TARGET)

    lowest = min(s.points for s in eligible)
    candidates = tuple(s.user_id for s in eligible if s.points == lowest)
    kind = OutcomeKind.SINGLE_LOSER if len(candidates) == 1 else OutcomeKind.TIEBREAK_NEEDED
    return PeriodOutcome(scores, candidates, kind)


def pick_loser(
    candidates: Sequence[UUID],
    choose: Callable[[Sequence[UUID]], UUID] = secrets.choice,
) -> UUID:
    """Pick one loser. Sorting first makes the pick depend only on `choose`."""
    if not candidates:
        raise ValueError("no candidates to pick from")
    return choose(sorted(candidates))


def _counts(member: MemberPeriodInput, bounds: PeriodBounds, t: datetime) -> bool:
    return (
        contains(bounds, t)
        and t >= member.joined_at
        and (member.removed_at is None or t < member.removed_at)
    )


def _score(member: MemberPeriodInput, target_n: int, bounds: PeriodBounds) -> MemberScore:
    counted = counted_check_ins(member, bounds)
    return MemberScore(
        user_id=member.user_id,
        state=member_state(member.joined_at, member.removed_at, member.excused, bounds),
        counted_check_ins=counted,
        points=min(target_n, counted),
    )


def _validate(target_n: int, bounds: PeriodBounds, members: Sequence[MemberPeriodInput]) -> None:
    if not MIN_TARGET_N <= target_n <= MAX_TARGET_N:
        raise ValueError(f"target_n must be {MIN_TARGET_N}-{MAX_TARGET_N}, got {target_n}")
    if len({m.user_id for m in members}) != len(members):
        raise ValueError("duplicate user_id in members")
    for m in members:
        if not in_member_set(m.joined_at, m.removed_at, bounds):
            raise ValueError(f"member {m.user_id} is not in the period's member set")
