from rest_framework import serializers
from apps.match.models import Match, MatchResult
from .models import PaidLeagueConfig, Payment, PaidBetRound, PaidPrizePool, PaidWinner

class LeagueMinimalSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    logo = serializers.URLField(source='logo_url')


class PaidLeagueConfigSerializer(serializers.ModelSerializer):
    league = LeagueMinimalSerializer(read_only=True)

    class Meta:
        model = PaidLeagueConfig
        fields = (
            'id', 'league', 'is_paid_mode_enabled', 'round_price_ars', 
            'league_price_ars', 'start_round_number',
        )


class PaymentSerializer(serializers.ModelSerializer):
    league_name = serializers.CharField(source='league.name', read_only=True)
    round_name = serializers.CharField(source='round.name', read_only=True)

    class Meta:
        model = Payment
        fields = (
            'id', 'payment_type', 'status', 'gross_amount_ars', 'league_name', 'round_name',
            'external_reference', 'creation_date',
        )


class PaymentPreferenceResponseSerializer(serializers.Serializer):
    """Response serializer for payment preference creation"""
    payment_id = serializers.IntegerField()
    external_reference = serializers.CharField()
    init_point = serializers.URLField()
    sandbox_init_point = serializers.URLField(required=False, allow_null=True)
    amount = serializers.CharField()
    rounds_count = serializers.IntegerField(required=False)


class PaymentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'status', 'external_reference', 'mp_payment_id', 'creation_date')


class PaidMatchResultSerializer(serializers.ModelSerializer):
    """Serializer for match results in paid mode (uses MatchResult)"""
    team_1_name = serializers.SerializerMethodField()
    team_2_name = serializers.SerializerMethodField()
    team_1_badge_url = serializers.SerializerMethodField()
    team_2_badge_url = serializers.SerializerMethodField()
    match_id = serializers.IntegerField(source='match.id', read_only=True)
    match_start_date = serializers.DateTimeField(source='match.start_date', read_only=True)

    class Meta:
        model = MatchResult
        fields = (
            'id', 'match_id', 'team_1_name', 'team_2_name', 'team_1_badge_url', 'points', 
            'team_2_badge_url', 'goals_team_1', 'goals_team_2', 'is_exact', 'match_start_date',
        )

    def get_team_1_name(self, obj):
        return obj.match.team_1.name

    def get_team_2_name(self, obj):
        return obj.match.team_2.name

    def get_team_1_badge_url(self, obj):
        return obj.match.team_1.badge_url

    def get_team_2_badge_url(self, obj):
        return obj.match.team_2.badge_url


class PaidMatchResultUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating match predictions (uses MatchResult)"""
    class Meta:
        model = MatchResult
        fields = ('goals_team_1', 'goals_team_2')

    def validate(self, data):
        # Check if match has started
        match = self.instance.match
        if match.match_state != Match.NOT_STARTED_MATCH:
            raise serializers.ValidationError(
                'Cannot update predictions after match has started'
            )
        return data


class PaidBetRoundSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    profile_image = serializers.SerializerMethodField()
    points = serializers.IntegerField(read_only=True)
    exact_results = serializers.IntegerField(read_only=True)
    round_id = serializers.IntegerField(source='round.id', read_only=True)
    round_name = serializers.CharField(source='round.name', read_only=True)

    class Meta:
        model = PaidBetRound
        fields = (
            'id', 'username', 'profile_image', 'points', 'exact_results', 'round_id',
            'round_name', 'winner_first', 'winner_second', 'winner_third',
        )

    def get_profile_image(self, obj):
        if obj.user.profile_image:
            return obj.user.profile_image.url
        return None


class PaidBetRoundDetailSerializer(PaidBetRoundSerializer):
    """Detailed serializer including match results (uses MatchResult)"""
    match_results = PaidMatchResultSerializer(many=True, read_only=True)

    class Meta(PaidBetRoundSerializer.Meta):
        fields = PaidBetRoundSerializer.Meta.fields + ('match_results',)


class PaidPrizePoolSerializer(serializers.ModelSerializer):
    league_name = serializers.CharField(source='league.name', read_only=True)
    round_name = serializers.CharField(source='round.name', read_only=True)

    class Meta:
        model = PaidPrizePool
        fields = (
            'id', 'league_name', 'round_name', 'is_league_pool', 'total_pool_ars', 'distributed',
        )


class LeaderboardEntrySerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    username = serializers.CharField()
    profile_image = serializers.URLField(allow_null=True)
    points = serializers.IntegerField()
    exact_results = serializers.IntegerField()
    winner_first = serializers.BooleanField()
    winner_second = serializers.BooleanField()
    winner_third = serializers.BooleanField()
