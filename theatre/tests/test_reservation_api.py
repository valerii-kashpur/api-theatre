from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from theatre.models import (
    Reservation,
    Performance,
    Play,
    TheatreHall,
    Genre,
    Actor,
    Ticket
)
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class ReservationViewSetUnauthenticatedTests(APITestCase):
    """Tests for ReservationViewSet with an unauthenticated user."""

    def setUp(self):
        self.client = APIClient()
        genre = Genre.objects.create(name="Drama")
        actor = Actor.objects.create(first_name="John", last_name="Doe")
        play = Play.objects.create(
            title="Silent Whispers",
            description="A dramatic tale"
        )
        play.genres.add(genre)
        play.actors.add(actor)
        theatre_hall = TheatreHall.objects.create(
            name="Main Hall",
            rows=20,
            seats_in_row=30
        )
        performance = Performance.objects.create(
            play=play,
            theatre_hall=theatre_hall,
            show_time="2025-03-01T19:00:00Z"
        )
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        reservation = Reservation.objects.create(user=user)
        Ticket.objects.create(
            row=1,
            seat=1,
            performance=performance,
            reservation=reservation
        )

    def test_reservation_list_unauthenticated(self):
        """Test that an unauthenticated user cannot list reservations (returns 401 Unauthorized)."""
        url = "/api/theatre/reservations/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )

    def test_reservation_create_unauthenticated(self):
        """Test that an unauthenticated user cannot create a reservation."""
        url = "/api/theatre/reservations/"
        performance = Performance.objects.get(show_time="2025-03-01T19:00:00Z")
        data = {
            "tickets": [
                {"row": 2, "seat": 2, "performance": performance.id}
            ]
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )
        self.assertEqual(
            Reservation.objects.count(),
            1
        )


class ReservationViewSetAuthenticatedUserTests(APITestCase):
    """Tests for ReservationViewSet with an authenticated non-admin user."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="userpass123"
        )

        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        genre = Genre.objects.create(name="Drama")
        actor = Actor.objects.create(first_name="John", last_name="Doe")
        play = Play.objects.create(
            title="Silent Whispers",
            description="A dramatic tale"
        )
        play.genres.add(genre)
        play.actors.add(actor)
        theatre_hall = TheatreHall.objects.create(
            name="Main Hall",
            rows=20,
            seats_in_row=30
        )
        performance = Performance.objects.create(
            play=play,
            theatre_hall=theatre_hall,
            show_time="2025-03-01T19:00:00Z"
        )
        self.reservation = Reservation.objects.create(user=self.user)
        Ticket.objects.create(
            row=1,
            seat=1,
            performance=performance,
            reservation=self.reservation
        )

    def test_reservation_list_authenticated(self):
        """Test that an authenticated non-admin user can list their reservations."""
        url = "/api/theatre/reservations/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data["results"]),
            1
        )
        self.assertEqual(response.data["results"][0]["tickets"][0]["row"], 1)
        self.assertEqual(response.data["results"][0]["tickets"][0]["seat"], 1)

    def test_reservation_create_authenticated(self):
        """Test that an authenticated non-admin user can create a reservation."""
        url = "/api/theatre/reservations/"
        performance = Performance.objects.get(show_time="2025-03-01T19:00:00Z")
        data = {
            "tickets": [
                {"row": 2, "seat": 2, "performance": performance.id}
            ]
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["tickets"]), 1)
        self.assertEqual(response.data["tickets"][0]["row"], 2)
        self.assertEqual(response.data["tickets"][0]["seat"], 2)

        reservation = Reservation.objects.filter(user=self.user).order_by(
            '-created_at'
        ).first()
        self.assertIsNotNone(reservation)
        self.assertEqual(
            Ticket.objects.filter(reservation=reservation).count(),
            1
        )

    def test_reservation_pay_authenticated(self):
        """Test that an authenticated non-admin user can initiate a payment for a reservation."""
        url = f"/api/theatre/reservations/{self.reservation.id}/pay/"
        data = {
            "payment_method_id": "pm_card_visa"
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("client_secret", response.data)
        self.assertIn("reservation_id", response.data)
        self.assertIn("payment_intent_id", response.data)
        self.reservation.refresh_from_db()
        self.assertEqual(
            self.reservation.payment_status,
            "paid"
        )

    def test_reservation_pay_authenticated_already_processed(self):
        """Test that an authenticated non-admin user cannot pay for an already processed reservation."""
        self.reservation.payment_status = "paid"
        self.reservation.save()
        url = f"/api/theatre/reservations/{self.reservation.id}/pay/"
        data = {
            "payment_method_id": "pm_card_visa"
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "Reservation already processed"
        )

    def test_reservation_pay_authenticated_invalid_payment_method(self):
        """Test that an authenticated non-admin user gets an error with an invalid payment method."""
        url = f"/api/theatre/reservations/{self.reservation.id}/pay/"
        data = {
            "payment_method_id": "invalid_pm_id"
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_reservation_confirm_payment_authenticated(self):
        """Test that an authenticated non-admin user can confirm a payment for a reservation."""
        pay_url = f"/api/theatre/reservations/{self.reservation.id}/pay/"
        pay_data = {
            "payment_method_id": "pm_card_visa"
        }
        pay_response = self.client.post(pay_url, pay_data, format="json")

        self.assertEqual(pay_response.status_code, status.HTTP_200_OK)
        payment_intent_id = pay_response.data["payment_intent_id"]

        confirm_url = f"/api/theatre/reservations/{self.reservation.id}/confirm-payment/"
        confirm_data = {
            "payment_intent_id": payment_intent_id
        }
        confirm_response = self.client.post(
            confirm_url,
            confirm_data,
            format="json"
        )

        self.assertEqual(confirm_response.status_code, status.HTTP_200_OK)
        self.assertEqual(confirm_response.data["status"], "success")
        self.assertEqual(confirm_response.data["payment_status"], "paid")
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.payment_status, "paid")

    def test_reservation_confirm_payment_authenticated_missing_payment_intent(
            self
    ):
        """Test that an authenticated non-admin user gets an error when confirming without payment intent ID."""
        url = f"/api/theatre/reservations/{self.reservation.id}/confirm-payment/"
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "Payment intent ID is required"
        )

    def test_reservation_confirm_payment_authenticated_invalid_payment_intent(
            self
    ):
        """Test that an authenticated non-admin user gets an error with an invalid payment intent ID."""
        url = f"/api/theatre/reservations/{self.reservation.id}/confirm-payment/"
        data = {
            "payment_intent_id": "invalid_pi_id"
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)


class ReservationViewSetAuthenticatedAdminTests(APITestCase):
    """Tests for ReservationViewSet with an authenticated admin user."""

    def setUp(self):
        self.user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )

        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        genre = Genre.objects.create(name="Drama")
        actor = Actor.objects.create(first_name="John", last_name="Doe")
        play = Play.objects.create(
            title="Silent Whispers",
            description="A dramatic tale"
        )
        play.genres.add(genre)
        play.actors.add(actor)
        theatre_hall = TheatreHall.objects.create(
            name="Main Hall",
            rows=20,
            seats_in_row=30
        )
        performance = Performance.objects.create(
            play=play,
            theatre_hall=theatre_hall,
            show_time="2025-03-01T19:00:00Z"
        )
        self.reservation = Reservation.objects.create(user=self.user)
        Ticket.objects.create(
            row=1,
            seat=1,
            performance=performance,
            reservation=self.reservation
        )

    def test_reservation_list_authenticated(self):
        """Test that an authenticated admin user can list their reservations."""
        url = "/api/theatre/reservations/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data["results"]),
            1
        )
        self.assertEqual(response.data["results"][0]["tickets"][0]["row"], 1)
        self.assertEqual(response.data["results"][0]["tickets"][0]["seat"], 1)

    def test_reservation_create_authenticated(self):
        """Test that an authenticated admin user can create a reservation."""
        url = "/api/theatre/reservations/"
        performance = Performance.objects.get(show_time="2025-03-01T19:00:00Z")
        data = {
            "tickets": [
                {"row": 2, "seat": 2, "performance": performance.id}
            ]
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["tickets"]), 1)
        self.assertEqual(response.data["tickets"][0]["row"], 2)
        self.assertEqual(response.data["tickets"][0]["seat"], 2)

        reservation = Reservation.objects.filter(user=self.user).order_by(
            '-created_at'
        ).first()
        self.assertIsNotNone(reservation)
        self.assertEqual(
            Ticket.objects.filter(reservation=reservation).count(),
            1
        )
