from datetime import datetime

import stripe
from django.conf import settings
from django.db.models import F, Count
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse, OpenApiExample
)
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication

from theatre.models import (
    Genre,
    Actor,
    TheatreHall,
    Play,
    Performance,
    Reservation
)
from theatre.pagination import (
    GenrePagination,
    ActorPagination,
    PlayPagination,
    PerformancePagination,
    ReservationPagination
)
from theatre.permissions import IsAdminOrIfAuthenticatedReadOnly
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
    ReservationListSerializer
)


class GenresViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Genre.objects.all()
    serializer_class = GenresSerializer
    pagination_class = GenrePagination
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class ActorViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    pagination_class = ActorPagination
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

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
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class PlayViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = Play.objects.all().prefetch_related("genres", "actors")
    serializer_class = PlaySerializer
    pagination_class = PlayPagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    @staticmethod
    def _params_to_ints(qs):
        """Converts a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        queryset = self.queryset

        if title:
            queryset = queryset.filter(title__icontains=title)
        if genres:
            genres_ids = self._params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres_ids)
        if actors:
            actors_ids = self._params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors_ids)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PlayDetailSerializer

        if self.action == "list":
            return PlayListSerializer

        return PlaySerializer

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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "title",
                description="Play title",
            ),
            OpenApiParameter(
                "genres",
                type={"type": "list", "items": {"type": "integer"}},
                description="Play genres",
            ),
            OpenApiParameter(
                "actors",
                type={"type": "list", "items": {"type": "integer"}},
                description="Play actors",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = (
        Performance.objects.all()
        .select_related(
            "play",
            "theatre_hall"
        )
        .annotate(
            tickets_available=(
                    F("theatre_hall__rows") * F("theatre_hall__seats_in_row")
                    - Count("tickets")
            )
        )
    )
    serializer_class = PerformanceSerializer
    pagination_class = PerformancePagination
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_queryset(self):
        date = self.request.query_params.get("date")
        play_id_str = self.request.query_params.get("play")

        queryset = self.queryset

        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(show_time__date=date)

        if play_id_str:
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
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Reservation.objects.prefetch_related(
        "tickets__performance_play",
        "tickets__performance__theatre_hall"
    )
    serializer_class = ReservationSerializer
    pagination_class = ReservationPagination
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer

        return ReservationSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        summary="Create a payment intent for the reservation"
                " using a test payment method",
        description="Initiates a payment intent for the specified reservation"
                    " using Stripe in test mode. Requires a"
                    " test payment method ID or token in the request body."
                    " Use Stripe's test payment method IDs"
                    " (e.g., 'pm_card_visa') for simulation."
                    " See https://stripe.com/docs/testing for test data."
                    " This endpoint is configured to only accept"
                    " card payments without redirects.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'payment_method_id': {
                        'type': 'string',
                        'description': 'The test payment method ID'
                                       ' or token from Stripe'
                                       ' (e.g., pm_card_visa for'
                                       ' a successful test payment)',
                        'example': 'pm_card_visa'
                    }
                },
                'required': ['payment_method_id']
            }
        },
        responses={
            200: OpenApiResponse(
                description="Payment intent created successfully"
                            " with attached payment method",
                examples=[
                    OpenApiExample(
                        'Example Response',
                        value={
                            'client_secret': 'pi_xxxx_secret_xxxx',
                            'reservation_id': 1,
                            'payment_intent_id': 'pi_xxxx'
                        },
                        summary="Successful payment intent creation"
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Bad request (e.g., reservation already processed,"
                            " invalid payment method, or Stripe error)",
                examples=[
                    OpenApiExample(
                        'Error Example',
                        value={'error': 'Reservation already processed'},
                        summary="Reservation already processed"
                    ),
                    OpenApiExample(
                        'Stripe Error Example',
                        value={'error': 'Invalid payment method'},
                        summary="Invalid payment method ID"
                    )
                ]
            ),
        },
    )
    @action(detail=True, methods=['POST'], url_path='pay')
    def pay(self, request, pk=None):
        reservation = self.get_object()
        if reservation.payment_status != 'pending':
            return Response(
                {"error": "Reservation already processed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment_method_id = request.data.get('payment_method_id')
        if not payment_method_id:
            return Response(
                {"error": "Payment method ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        amount = 1000  # 10.00 USD in cents
        currency = 'usd'

        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                payment_method=payment_method_id,
                confirm=True,
                automatic_payment_methods={
                    'enabled': True,
                    'allow_redirects': 'never'
                },
            )

            if payment_intent.status == 'succeeded':
                reservation.payment_status = 'paid'
            else:
                reservation.payment_status = 'failed'
            reservation.save()

            return Response(
                {
                    'client_secret': payment_intent.client_secret,
                    'reservation_id': reservation.id,
                    'payment_intent_id': payment_intent.id,
                    "amount": payment_intent.amount
                }, status=status.HTTP_200_OK
            )

        except stripe.error.StripeError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary="Confirm the payment for the reservation",
        description="Confirms a payment intent for the specified reservation"
                    " using Stripe in test mode. Requires the payment intent"
                    " ID from the 'pay' endpoint. The 'id' in the URL path"
                    " must be the reservation ID (an integer)."
                    " Since the payment method is already attached in"
                    " the 'pay' endpoint, this step simply verifies"
                    " the payment status.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location="path",
                description="The unique integer ID of the reservation"
                            " to confirm payment for (e.g., 1)",
                required=True,
            ),
        ],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'payment_intent_id': {
                        'type': 'string',
                        'description': 'The ID of the'
                                       ' Payment Intent from Stripe'
                                       ' (e.g., pi_3QwMRqEqE7060X0V8SCABXKv).'
                                       ' Use the ID returned from the'
                                       ' "pay" endpoint.',
                        'example': 'pi_3QwMRqEqE7060X0V8SCABXKv'
                    }
                },
                'required': ['payment_intent_id']
            }
        },
        responses={
            200: OpenApiResponse(
                description="Payment confirmed successfully",
                examples=[
                    OpenApiExample(
                        'Example Response',
                        value={
                            'status': 'success',
                            'payment_status': 'paid',
                            'payment_intent': {
                                'id': 'pi_3QwMRqEqE7060X0V8SCABXKv',
                                'status': 'succeeded'
                            }
                        },
                        summary="Successful payment confirmation"
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Bad request (e.g., invalid payment intent ID,"
                            " reservation not found, or Stripe error)",
                examples=[
                    OpenApiExample(
                        'Error Example',
                        value={'error': 'Payment intent ID is required'},
                        summary="Missing payment intent ID"
                    ),
                    OpenApiExample(
                        'Stripe Error Example',
                        value={'error': 'Payment intent not found'},
                        summary="Invalid payment intent ID"
                    )
                ]
            ),
        },
    )
    @action(detail=True, methods=['POST'], url_path='confirm-payment')
    def confirm_payment(self, request, pk=None):
        reservation = self.get_object()
        payment_intent_id = request.data.get('payment_intent_id')

        if not payment_intent_id:
            return Response(
                {"error": "Payment intent ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if payment_intent.status == 'requires_confirmation':
                stripe.PaymentIntent.confirm(payment_intent_id)

            if payment_intent.status == 'succeeded':
                reservation.payment_status = 'paid'
            else:
                reservation.payment_status = 'failed'
            reservation.save()

            return Response(
                {
                    'status': 'success',
                    'payment_status': reservation.payment_status,
                    'payment_intent': stripe.PaymentIntent.retrieve(
                        payment_intent_id
                    ),
                }, status=status.HTTP_200_OK
            )

        except (Reservation.DoesNotExist, stripe.error.StripeError) as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
