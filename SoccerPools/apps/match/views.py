from rest_framework import status, permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, get_list_or_404
from .serializers import MatchResultSerializer
from .models import MatchResult


class MatchResultsListCreateApiView(generics.ListCreateAPIView):
    permission_class = (permissions.IsAuthenticated,)
    serializer_class = MatchResultSerializer

    def get_queryset(self):
        round_id = self.request.query_params.get('round_id')
        match_results = MatchResult.objects.filter(bet__round__id=round_id)
        return match_results
    
    def post(self, request):
        serializer = MatchResultSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

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