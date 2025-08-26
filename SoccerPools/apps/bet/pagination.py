from rest_framework.pagination import CursorPagination

class BetRoundLeadersCursorPagination(CursorPagination):
    page_size = 25
    ordering = ('-matches_points', '-exact_results_count', 'id')