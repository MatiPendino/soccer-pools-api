from rest_framework import status, permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response
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
        serializer = MatchResultSerializer(request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)