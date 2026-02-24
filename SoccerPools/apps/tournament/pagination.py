from rest_framework.pagination import PageNumberPagination

class TournamentPagination(PageNumberPagination):
    page_size = 30
