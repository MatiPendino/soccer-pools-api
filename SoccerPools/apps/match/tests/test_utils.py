import unittest
from apps.match.utils import get_match_result_points

class UtilsTests(unittest.TestCase):
    def test_get_match_result_points(self):
        result_1 = get_match_result_points(
            user_goals_team_1=1,
            user_goals_team_2=1,
            original_goals_team_1=1,
            original_goals_team_2=1
        )
        self.assertEqual(result_1, 3)

        result_2 = get_match_result_points(
            user_goals_team_1=2,
            user_goals_team_2=1,
            original_goals_team_1=1,
            original_goals_team_2=0
        )
        self.assertEqual(result_2, 1)

        result_3 = get_match_result_points(
            user_goals_team_1=0,
            user_goals_team_2=1,
            original_goals_team_1=0,
            original_goals_team_2=4
        )
        self.assertEqual(result_3, 1)

        result_4 = get_match_result_points(
            user_goals_team_1=0,
            user_goals_team_2=1,
            original_goals_team_1=0,
            original_goals_team_2=0
        )
        self.assertEqual(result_4, 0)

        result_5 = get_match_result_points(
            user_goals_team_1=None,
            user_goals_team_2=1,
            original_goals_team_1=0,
            original_goals_team_2=1
        )
        self.assertEqual(result_5, 0)

        result_6 = get_match_result_points(
            user_goals_team_1=None,
            user_goals_team_2=None,
            original_goals_team_1=0,
            original_goals_team_2=0
        )
        self.assertEqual(result_6, 0)