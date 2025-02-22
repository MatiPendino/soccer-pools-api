from rest_framework import status, permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_list_or_404, get_object_or_404
from .serializers import MatchResultSerializer
from .models import MatchResult, Match


class MatchResultsListCreateApiView(generics.ListCreateAPIView):
    permission_class = (permissions.IsAuthenticated,)
    serializer_class = MatchResultSerializer

    def get_queryset(self):
        round_id = self.request.query_params.get('round_id')
        match_results = MatchResult.objects.filter(
            bet_round__round__id=round_id,
            bet_round__bet_league__user=self.request.user,
            state=True
        ).order_by('match__start_date')
        return match_results
    

class MatchResultsUpdateApiView(APIView):
    permission_class = (permissions.IsAuthenticated,)

    def post(self, request):
        match_results_data = request.data.get('matchResults')

        match_results_ids = [match_result['id'] for match_result in match_results_data]
        match_results = get_list_or_404(MatchResult, id__in=match_results_ids)
        
        # Create a mapping of match result objects by ID
        match_result_map = {match_result.id: match_result for match_result in match_results}

        # Update the fields in bulk
        for result_data in match_results_data:
            match_result = match_result_map.get(result_data['id'])
            if match_result:
                match_result.goals_team_1 = result_data['goals_team_1']
                match_result.goals_team_2 = result_data['goals_team_2']

        MatchResult.objects.bulk_update(match_results, ['goals_team_1', 'goals_team_2'])

        return Response({'success': 'Match results updated successfully!'})
    

class MatchResultOriginalRetrieveApiView(APIView):
    permission_class = (permissions.IsAuthenticated,)

    def get(self, request, match_id):
        match = get_object_or_404(Match, id=match_id)
        original_match_result = MatchResult.objects.filter( 
            state=True, 
            match=match,
            original_result=True
        ).first()
        if original_match_result:
            serializer = MatchResultSerializer(original_match_result)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(None, status=status.HTTP_204_NO_CONTENT)