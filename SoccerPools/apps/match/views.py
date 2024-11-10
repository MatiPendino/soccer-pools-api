from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import MatchResultSerializer


class MatchResultsCreateApiView(APIView):
    permission_class = (permissions.IsAuthenticated,)
    
    def post(self, request):
        serializer = MatchResultSerializer(request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)