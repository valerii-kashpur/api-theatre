import os

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from theatre.models import Performance, Play, TheatreHall, Genre, Actor
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io

User = get_user_model()


class PerformanceViewSetUnauthenticatedTests(APITestCase):
    """Tests for PerformanceViewSet with an unauthenticated user."""

    def setUp(self):
        self.client = APIClient()
        genre = Genre.objects.create(name="Drama")
        actor = Actor.objects.create(first_name="John", last_name="Doe")
        play = Play.objects.create(
            title="Silent Whispers", description="A dramatic tale"
        )
        play.genres.add(genre)
        play.actors.add(actor)
        theatre_hall = TheatreHall.objects.create(
            name="Main Hall", rows=20, seats_in_row=30
        )
        self.performance = Performance.objects.create(
            play=play,
            theatre_hall=theatre_hall,
            show_time="2025-03-01T19:00:00Z",
        )

    def test_performance_list_unauthenticated(self):
        """Test that an unauthenticated
         user cannot list performances (returns 401 Unauthorized)."""
        url = "/api/theatre/performances/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided.",
        )

    def test_performance_retrieve_unauthenticated(self):
        """Test that an unauthenticated
         user cannot retrieve a performance (returns 401 Unauthorized)."""
        url = f"/api/theatre/performances/{self.performance.id}/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided.",
        )

    def test_performance_create_unauthenticated(self):
        """Test that an unauthenticated user cannot create a performance."""
        url = "/api/theatre/performances/"
        play = Play.objects.get(title="Silent Whispers")
        theatre_hall = TheatreHall.objects.get(name="Main Hall")
        data = {
            "play": play.id,
            "theatre_hall": theatre_hall.id,
            "show_time": "2025-03-02T18:00:00Z",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided.",
        )
        self.assertEqual(Performance.objects.count(), 1)


class PerformanceViewSetAuthenticatedUserTests(APITestCase):
    """Tests for PerformanceViewSet with an authenticated non-admin user."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="userpass123"
        )

        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        genre = Genre.objects.create(name="Drama")
        actor = Actor.objects.create(first_name="John", last_name="Doe")
        play = Play.objects.create(
            title="Silent Whispers", description="A dramatic tale"
        )
        play.genres.add(genre)
        play.actors.add(actor)
        theatre_hall = TheatreHall.objects.create(
            name="Main Hall", rows=20, seats_in_row=30
        )
        self.performance = Performance.objects.create(
            play=play,
            theatre_hall=theatre_hall,
            show_time="2025-03-01T19:00:00Z",
        )

    def test_performance_list_authenticated(self):
        """Test that an authenticated non-admin user can list performances."""
        url = "/api/theatre/performances/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["play_title"], "Silent Whispers"
        )

    def test_performance_retrieve_authenticated(self):
        """Test that an authenticated non-admin
         user can retrieve a performance."""
        url = f"/api/theatre/performances/{self.performance.id}/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["play"]["title"], "Silent Whispers")
        self.assertEqual(response.data["theatre_hall"]["name"], "Main Hall")
        self.assertEqual(
            str(response.data["show_time"]), "2025-03-01T19:00:00Z"
        )

    def test_performance_create_authenticated(self):
        """Test that an authenticated non-admin
         user cannot create a performance (returns 403 Forbidden)."""
        url = "/api/theatre/performances/"
        play = Play.objects.get(title="Silent Whispers")
        theatre_hall = TheatreHall.objects.get(name="Main Hall")
        data = {
            "play": play.id,
            "theatre_hall": theatre_hall.id,
            "show_time": "2025-03-02T18:00:00Z",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )
        self.assertEqual(Performance.objects.count(), 1)

    def test_performance_upload_image_authenticated(self):
        """Test that an authenticated non-admin
         user cannot upload an image (returns 403 Forbidden)."""
        url = f"/api/theatre/performances/{self.performance.id}/upload-image/"
        # Create a test image in memory using PIL
        img = Image.new("RGB", (10, 10))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG")
        img_byte_arr = img_byte_arr.getvalue()
        image = SimpleUploadedFile(
            "test_image.jpg", img_byte_arr, content_type="image/jpeg"
        )
        data = {"image": image}
        response = self.client.post(url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )


class PerformanceViewSetAuthenticatedAdminTests(APITestCase):
    """Tests for PerformanceViewSet with an authenticated admin user."""

    def setUp(self):
        self.user = User.objects.create_superuser(
            email="admin@example.com", password="adminpass123"
        )

        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        genre = Genre.objects.create(name="Drama")
        actor = Actor.objects.create(first_name="John", last_name="Doe")
        play = Play.objects.create(
            title="Silent Whispers", description="A dramatic tale"
        )
        play.genres.add(genre)
        play.actors.add(actor)
        theatre_hall = TheatreHall.objects.create(
            name="Main Hall", rows=20, seats_in_row=30
        )
        self.performance = Performance.objects.create(
            play=play,
            theatre_hall=theatre_hall,
            show_time="2025-03-01T19:00:00Z",
        )

    def test_performance_list_authenticated(self):
        """Test that an authenticated admin user can list performances."""
        url = "/api/theatre/performances/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["play_title"], "Silent Whispers"
        )

    def test_performance_retrieve_authenticated(self):
        """Test that an authenticated admin user can retrieve a performance."""
        url = f"/api/theatre/performances/{self.performance.id}/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["play"]["title"], "Silent Whispers"
        )
        self.assertEqual(
            response.data["theatre_hall"]["name"], "Main Hall"
        )
        self.assertEqual(
            str(response.data["show_time"]), "2025-03-01T19:00:00Z"
        )
        self.assertEqual(
            response.data["taken_places"], []
        )  # No tickets by default

    def test_performance_create_authenticated(self):
        """Test that an authenticated admin user can create a performance."""
        url = "/api/theatre/performances/"
        play = Play.objects.get(title="Silent Whispers")
        theatre_hall = TheatreHall.objects.get(name="Main Hall")
        data = {
            "play": play.id,
            "theatre_hall": theatre_hall.id,
            "show_time": "2025-03-02T18:00:00Z",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["play"], play.id)
        self.assertEqual(response.data["theatre_hall"], theatre_hall.id)
        self.assertEqual(
            str(response.data["show_time"]), "2025-03-02T18:00:00Z"
        )

        performance = Performance.objects.get(show_time="2025-03-02T18:00:00Z")
        self.assertIsNotNone(performance)

    def test_performance_upload_image_authenticated(self):
        """Test that an authenticated admin
         user can upload an image for a performance."""
        url = f"/api/theatre/performances/{self.performance.id}/upload-image/"
        play = Play.objects.get(title="Silent Whispers")
        theatre_hall = TheatreHall.objects.get(name="Main Hall")
        img = Image.new("RGB", (10, 10))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG")
        img_byte_arr = img_byte_arr.getvalue()
        image = SimpleUploadedFile(
            "test_image.jpg", img_byte_arr, content_type="image/jpeg"
        )
        data = {
            "image": image,
            "play": play.id,
            "theatre_hall": theatre_hall.id,
            "show_time": "2025-03-02T18:00:00Z",
        }
        response = self.client.post(url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("image", response.data)
        self.performance.refresh_from_db()
        self.assertIsNotNone(self.performance.image)
        self.assertTrue(os.path.exists(self.performance.image.path))
