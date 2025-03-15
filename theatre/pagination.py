from rest_framework.pagination import PageNumberPagination


class ActorPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 20


class GenrePagination(PageNumberPagination):
    page_size = 10
    max_page_size = 20


class PlayPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 20


class PerformancePagination(PageNumberPagination):
    page_size = 10
    max_page_size = 20


class ReservationPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 20
