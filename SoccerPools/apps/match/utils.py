
def get_match_result_points(user_goals_team_1, user_goals_team_2, original_goals_team_1,
    original_goals_team_2):
    if (
        user_goals_team_1 == original_goals_team_1 and 
        user_goals_team_2 == original_goals_team_2
    ):
        return 3
    elif (
        (
            user_goals_team_1 - user_goals_team_2 > 0 and
            original_goals_team_1 - original_goals_team_2 > 0
        )
        or
        (
            user_goals_team_1 - user_goals_team_2 < 0 and
            original_goals_team_1 - original_goals_team_2 < 0
        )
        or (
            user_goals_team_1 - user_goals_team_2 == 0 and
            original_goals_team_1 - original_goals_team_2 == 0
        )
    ):
        return 1
    else:
        return 0