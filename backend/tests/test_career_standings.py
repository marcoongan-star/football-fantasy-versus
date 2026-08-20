from app.career_standings import CareerResult, build_career_table


def test_career_table_uses_three_one_zero_and_goal_difference() -> None:
    table = build_career_table(
        (
            CareerResult("marco", "alex", 2, 1),
            CareerResult("alex", "sam", 1, 1),
            CareerResult("sam", "marco", 3, 0),
        )
    )

    assert [row.user_id for row in table] == ["sam", "marco", "alex"]
    assert [(row.points, row.goal_difference) for row in table] == [
        (4, 3),
        (3, -2),
        (1, -1),
    ]


def test_head_to_head_breaks_an_exact_primary_tie() -> None:
    table = build_career_table(
        (
            CareerResult("marco", "alex", 1, 0),
            CareerResult("marco", "sam", 0, 1),
            CareerResult("alex", "jamie", 1, 0),
            CareerResult("sam", "jamie", 1, 0),
        )
    )

    tied = [row for row in table if row.user_id in {"marco", "alex"}]
    assert [(row.user_id, row.head_to_head_points) for row in tied] == [
        ("marco", 3),
        ("alex", 0),
    ]
    assert tied[0].points == tied[1].points == 3
    assert tied[0].goal_difference == tied[1].goal_difference == 0


def test_active_manager_with_no_matches_still_appears() -> None:
    table = build_career_table((), participant_ids=("marco", "alex"))

    assert [row.user_id for row in table] == ["alex", "marco"]
    assert all(row.played == 0 and row.points == 0 for row in table)
