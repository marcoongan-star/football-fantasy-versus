from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class CareerResult:
    home_user_id: str
    away_user_id: str
    home_goals: int
    away_goals: int

    def __post_init__(self) -> None:
        if self.home_user_id == self.away_user_id:
            raise ValueError("a manager cannot play themselves")
        if self.home_goals < 0 or self.away_goals < 0:
            raise ValueError("goals cannot be negative")


@dataclass(frozen=True)
class CareerStanding:
    position: int
    user_id: str
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    goal_difference: int = 0
    points: int = 0
    head_to_head_points: int = 0


def _points_for(result: CareerResult, user_id: str) -> int:
    if result.home_goals == result.away_goals:
        return 1
    home_won = result.home_goals > result.away_goals
    return 3 if (user_id == result.home_user_id) == home_won else 0


def build_career_table(
    results: tuple[CareerResult, ...],
    participant_ids: tuple[str, ...] = (),
) -> tuple[CareerStanding, ...]:
    """Derive a career-only table; stored match facts remain the source of truth."""
    ids = set(participant_ids)
    for result in results:
        ids.update((result.home_user_id, result.away_user_id))
    rows = {user_id: CareerStanding(position=0, user_id=user_id) for user_id in ids}

    for result in results:
        for user_id, goals_for, goals_against in (
            (result.home_user_id, result.home_goals, result.away_goals),
            (result.away_user_id, result.away_goals, result.home_goals),
        ):
            current = rows[user_id]
            won = goals_for > goals_against
            drawn = goals_for == goals_against
            rows[user_id] = replace(
                current,
                played=current.played + 1,
                wins=current.wins + int(won),
                draws=current.draws + int(drawn),
                losses=current.losses + int(not won and not drawn),
                goals_for=current.goals_for + goals_for,
                goals_against=current.goals_against + goals_against,
                goal_difference=current.goal_difference + goals_for - goals_against,
                points=current.points + (3 if won else 1 if drawn else 0),
            )

    primary_groups: dict[tuple[int, int, int], list[CareerStanding]] = {}
    for row in rows.values():
        primary_groups.setdefault(
            (row.points, row.goal_difference, row.goals_for), []
        ).append(row)

    ordered: list[CareerStanding] = []
    for primary_key in sorted(primary_groups, reverse=True):
        group = primary_groups[primary_key]
        tied_ids = {row.user_id for row in group}
        head_to_head = {user_id: 0 for user_id in tied_ids}
        if len(group) > 1:
            for result in results:
                if {result.home_user_id, result.away_user_id} <= tied_ids:
                    head_to_head[result.home_user_id] += _points_for(
                        result, result.home_user_id
                    )
                    head_to_head[result.away_user_id] += _points_for(
                        result, result.away_user_id
                    )
        group_with_tiebreak = [
            replace(row, head_to_head_points=head_to_head[row.user_id]) for row in group
        ]
        ordered.extend(
            sorted(
                group_with_tiebreak,
                key=lambda row: (-row.head_to_head_points, row.user_id),
            )
        )

    return tuple(replace(row, position=index) for index, row in enumerate(ordered, 1))
