import datetime
from django.test import TestCase
from django.utils import timezone
from apps.match.models import Match
from apps.league.factories import LeagueFactory, RoundFactory
from apps.match.factories import MatchFactory

class UpdateStartDateTest(TestCase):
    def test_update_start_date_sets_earliest_match_date(self):
        league = LeagueFactory()
        round = RoundFactory(league=league, start_date=None)
        match1 = MatchFactory(
            round=round, state=True, 
            start_date=timezone.datetime(
                2024, 6, 1, 10, 0, tzinfo=datetime.timezone.utc
            ), 
            match_state=Match.NOT_STARTED_MATCH
        )
        match2 = MatchFactory(
            round=round, state=True, 
            start_date=timezone.datetime(
                2024, 6, 2, 10, 0, tzinfo=datetime.timezone.utc
            ), 
            match_state=Match.PENDING_MATCH
        )
        match3 = MatchFactory(
            round=round, state=True, 
            start_date=timezone.datetime(
                2024, 5, 30, 9, 0, tzinfo=datetime.timezone.utc
            ), 
            match_state=Match.FINALIZED_MATCH
        )
        round.update_start_date()
        round.refresh_from_db()
        self.assertEqual(
            round.start_date, timezone.datetime(2024, 5, 30, 9, 0, tzinfo=datetime.timezone.utc)
        )

    def test_update_start_date_ignores_matches_with_state_false(self):
        league = LeagueFactory()
        round = RoundFactory(league=league, start_date=None)
        match1 = MatchFactory(
            round=round, state=False,
            start_date=timezone.datetime(
                2024, 6, 1, 10, 0, tzinfo=datetime.timezone.utc
            ), 
            match_state=Match.NOT_STARTED_MATCH
        )
        match2 = MatchFactory(
            round=round, state=False,
            start_date=timezone.datetime(
                2024, 6, 2, 10, 0, tzinfo=datetime.timezone.utc
            ), 
            match_state=Match.PENDING_MATCH
        )
        round.update_start_date()
        round.refresh_from_db()
        self.assertIsNone(round.start_date)

    def test_update_start_date_ignores_matches_with_start_date_none(self):
        league = LeagueFactory()
        round = RoundFactory(league=league, start_date=None)
        match1 = MatchFactory(
            round=round, start_date=None, state=True, match_state=Match.NOT_STARTED_MATCH
        )
        match2 = MatchFactory(
            round=round, start_date=None, state=True, match_state=Match.PENDING_MATCH
        )
        round.update_start_date()
        round.refresh_from_db()
        self.assertIsNone(round.start_date)

    def test_update_start_date_does_not_change_if_already_set(self):
        league = LeagueFactory()
        round = RoundFactory(
            league=league, 
            start_date=timezone.datetime(2024, 5, 30, 9, 0, tzinfo=datetime.timezone.utc)
        )
        match1 = MatchFactory(
            round=round, state=True,
            start_date=timezone.datetime(2024, 5, 30, 9, 0, tzinfo=datetime.timezone.utc), 
            match_state=Match.NOT_STARTED_MATCH
        )
        match2 = MatchFactory(
            round=round, state=True, 
            start_date=timezone.datetime(2024, 6, 1, 10, 0, tzinfo=datetime.timezone.utc), 
            match_state=Match.PENDING_MATCH
        )
        round.update_start_date()
        round.refresh_from_db()
        self.assertEqual(
            round.start_date, 
            timezone.datetime(2024, 5, 30, 9, 0, tzinfo=datetime.timezone.utc)
        )

    def test_update_start_date_does_not_change_if_invalid_match_state(self):
        league = LeagueFactory()
        round = RoundFactory(
            league=league, 
            start_date=timezone.datetime(2024, 5, 30, 9, 0, tzinfo=datetime.timezone.utc)
        )
        match1 = MatchFactory(
            round=round, state=True, 
            start_date=timezone.datetime(2024, 4, 30, 9, 0, tzinfo=datetime.timezone.utc), 
            match_state=Match.POSTPONED_MATCH
        )
        match2 = MatchFactory(
            round=round, state=True,
            start_date=timezone.datetime(2024, 2, 1, 10, 0, tzinfo=datetime.timezone.utc), 
            match_state=Match.CANCELLED_MATCH
        )
        round.update_start_date()
        round.refresh_from_db()
        self.assertEqual(
            round.start_date, 
            timezone.datetime(2024, 5, 30, 9, 0, tzinfo=datetime.timezone.utc)
        )
