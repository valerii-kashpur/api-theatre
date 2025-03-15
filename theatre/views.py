from datetime import datetime

import stripe
from django.db.models import F, Count
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from theatre.models import (
    Genre,
    Actor,
    TheatreHall,
    Play,
    Performance,
    Reservation,
)
from theatre.pagination import (
    GenrePagination,
    ActorPagination,
    PlayPagination,
    PerformancePagination,
    ReservationPagination,
)
from theatre.schemas import (
    play_list_schema,
    reservation_pay_schema,
    reservation_confirm_payment_schema
)
from theatre.serializers import (
    GenresSerializer,
    ActorSerializer,
    TheatreHallSerializer,
    PlaySerializer,
    PlayDetailSerializer,
    PlayListSerializer,
    PerformanceSerializer,
    PerformanceDetailSerializer,
    PerformanceListSerializer,
    ReservationSerializer,
    ReservationListSerializer,
)


class GenresViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Genre.objects.all()
    serializer_class = GenresSerializer
    pagination_class = GenrePagination


class ActorViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    pagination_class = ActorPagination

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading image to specific Actor"""
        movie = self.get_object()
        serializer = self.get_serializer(movie, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TheatreHallViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer


class PlayViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = Play.objects.prefetch_related("genres", "actors")
    serializer_class = PlaySerializer
    pagination_class = PlayPagination

    @staticmethod
    def _params_to_ints(qs):
        """Converts a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        queryset = super().get_queryset()

        if title := self.request.query_params.get("title"):
            queryset = queryset.filter(title__icontains=title)
        if genres := self.request.query_params.get("genres"):
            genres_ids = self._params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres_ids)
        if actors := self.request.query_params.get("actors"):
            actors_ids = self._params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors_ids)

        return queryset.distinct()

    def get_serializer_class(self):
        serializer_class = super().get_serializer_class()
        if self.action == "retrieve":
            serializer_class = PlayDetailSerializer

        if self.action == "list":
            serializer_class = PlayListSerializer

        return serializer_class

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading image to specific Play"""
        movie = self.get_object()
        serializer = self.get_serializer(movie, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @play_list_schema
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = (
        Performance.objects.all()
        .select_related("play", "theatre_hall")
        .annotate(
            tickets_available=(
                    F("theatre_hall__rows") * F("theatre_hall__seats_in_row")
                    - Count("tickets")
            )
        )
    )
    serializer_class = PerformanceSerializer
    pagination_class = PerformancePagination

    def get_queryset(self):
        queryset = self.queryset

        if date := self.request.query_params.get("date"):
            date = datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(show_time__date=date)

        if play_id_str := self.request.query_params.get("play"):
            queryset = queryset.filter(play_id=int(play_id_str))

        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PerformanceDetailSerializer

        if self.action == "list":
            return PerformanceListSerializer

        return PerformanceSerializer

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading image to specific Performance"""
        movie = self.get_object()
        serializer = self.get_serializer(movie, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReservationViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, GenericViewSet
):
    queryset = Reservation.objects.prefetch_related(
        "tickets__performance_play", "tickets__performance__theatre_hall"
    )
    serializer_class = ReservationSerializer
    pagination_class = ReservationPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer

        return ReservationSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @reservation_pay_schema
    @action(detail=True, methods=["POST"], url_path="pay")
    def pay(self, request, pk=None):
        reservation = self.get_object()
        if reservation.payment_status != "pending":
            return Response(
                {"error": "Reservation already processed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment_method_id = request.data.get("payment_method_id")
        if not payment_method_id:
            return Response(
                {"error": "Payment method ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        amount = 1000  # 10.00 USD in cents
        currency = "usd"

        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                payment_method=payment_method_id,
                confirm=True,
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "never",
                },
            )

            if payment_intent.status == "succeeded":
                reservation.payment_status = "paid"
            else:
                reservation.payment_status = "failed"
            reservation.save()

            return Response(
                {
                    "client_secret": payment_intent.client_secret,
                    "reservation_id": reservation.id,
                    "payment_intent_id": payment_intent.id,
                    "amount": payment_intent.amount,
                },
                status=status.HTTP_200_OK,
            )

        except stripe.error.StripeError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

    @reservation_confirm_payment_schema
    @action(detail=True, methods=["POST"], url_path="confirm-payment")
    def confirm_payment(self, request, pk=None):
        reservation = self.get_object()
        payment_intent_id = request.data.get("payment_intent_id")

        if not payment_intent_id:
            return Response(
                {"error": "Payment intent ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if payment_intent.status == "requires_confirmation":
                stripe.PaymentIntent.confirm(payment_intent_id)

            if payment_intent.status == "succeeded":
                reservation.payment_status = "paid"
            else:
                reservation.payment_status = "failed"
            reservation.save()

            return Response(
                {
                    "status": "success",
                    "payment_status": reservation.payment_status,
                    "payment_intent": stripe.PaymentIntent.retrieve(
                        payment_intent_id
                    ),
                },
                status=status.HTTP_200_OK,
            )

        except (Reservation.DoesNotExist, stripe.error.StripeError) as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
