import io

from PIL import Image
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from theatre.models import Play, Genre, Actor
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.uploadedfile import SimpleUploadedFile
import os

User = get_user_model()


class PlayViewSetUnauthenticatedTests(APITestCase):
    """Tests for PlayViewSet with an unauthenticated user."""

    def setUp(self):
        self.client = APIClient()
        genre = Genre.objects.create(name="Drama")
        actor = Actor.objects.create(first_name="John", last_name="Doe")
        self.play = Play.objects.create(
            title="Silent Whispers", description="A dramatic tale"
        )
        self.play.genres.add(genre)
        self.play.actors.add(actor)

    def test_play_list_unauthenticated(self):
        """Test that an unauthenticated user
         cannot list plays (returns 401 Unauthorized)."""
        url = "/api/theatre/plays/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided.",
        )

    def test_play_retrieve_unauthenticated(self):
        """Test that an unauthenticated user
         cannot retrieve a play (returns 401 Unauthorized)."""
        url = f"/api/theatre/plays/{self.play.id}/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided.",
        )

    def test_play_create_unauthenticated(self):
        """Test that an unauthenticated user cannot create a play."""
        url = "/api/theatre/plays/"
        actor = Actor.objects.get(first_name="John", last_name="Doe")
        data = {
            "title": "New Play",
            "description": "A new story",
            "genres": [Genre.objects.get(name="Drama").id],
            "actors": [actor.id],
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided.",
        )
        self.assertEqual(
            Play.objects.count(), 1
        )  # Ensure no new play was created


class PlayViewSetAuthenticatedUserTests(APITestCase):
    """Tests for PlayViewSet with an authenticated non-admin user."""

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
        self.play = Play.objects.create(
            title="Silent Whispers", description="A dramatic tale"
        )
        self.play.genres.add(genre)
        self.play.actors.add(actor)

    def test_play_list_authenticated(self):
        """Test that an authenticated non-admin user can list plays."""
        url = "/api/theatre/plays/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["title"], "Silent Whispers"
        )

    def test_play_retrieve_authenticated(self):
        """Test that an authenticated non-admin user can retrieve a play."""
        url = f"/api/theatre/plays/{self.play.id}/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Silent Whispers")
        self.assertEqual(response.data["description"], "A dramatic tale")
        self.assertEqual(len(response.data["genres"]), 1)
        self.assertEqual(response.data["genres"][0]["name"], "Drama")
        self.assertEqual(len(response.data["actors"]), 1)
        self.assertEqual(
            response.data["actors"][0]["full_name"], "John Doe"
        )

    def test_play_create_authenticated(self):
        """Test that an authenticated non-admin
         user cannot create a play (returns 403 Forbidden)."""
        url = "/api/theatre/plays/"
        actor = Actor.objects.get(first_name="John", last_name="Doe")
        data = {
            "title": "New Play",
            "description": "A new story",
            "genres": [Genre.objects.get(name="Drama").id],
            "actors": [actor.id],
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )
        self.assertEqual(Play.objects.count(), 1)

    def test_play_upload_image_authenticated(self):
        """Test that an authenticated non-admin
         user cannot upload an image (returns 403 Forbidden)."""
        url = f"/api/theatre/plays/{self.play.id}/upload-image/"
        actor = Actor.objects.get(first_name="John", last_name="Doe")
        img = Image.new("RGB", (10, 10))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG")
        img_byte_arr = img_byte_arr.getvalue()
        image = SimpleUploadedFile(
            "test_image.jpg", img_byte_arr, content_type="image/jpeg"
        )
        data = {
            "image": image,
            "description": "A new story",
            "title": "New Play",
            "genres": [Genre.objects.get(name="Drama").id],
            "actors": actor.id,
        }
        response = self.client.post(url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )


class PlayViewSetAuthenticatedAdminTests(APITestCase):
    """Tests for PlayViewSet with an authenticated admin user."""

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
        self.play = Play.objects.create(
            title="Silent Whispers", description="A dramatic tale"
        )
        self.play.genres.add(genre)
        self.play.actors.add(actor)

    def test_play_list_authenticated(self):
        """Test that an authenticated admin user can list plays."""
        url = "/api/theatre/plays/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["title"], "Silent Whispers"
        )

    def test_play_retrieve_authenticated(self):
        """Test that an authenticated admin user can retrieve a play."""
        url = f"/api/theatre/plays/{self.play.id}/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Silent Whispers")
        self.assertEqual(response.data["description"], "A dramatic tale")
        self.assertEqual(len(response.data["genres"]), 1)
        self.assertEqual(response.data["genres"][0]["name"], "Drama")
        self.assertEqual(len(response.data["actors"]), 1)
        self.assertEqual(
            response.data["actors"][0]["full_name"], "John Doe"
        )

    def test_play_create_authenticated(self):
        """Test that an authenticated admin user can create a play."""
        url = "/api/theatre/plays/"
        actor = Actor.objects.get(first_name="John", last_name="Doe")
        data = {
            "title": "New Play",
            "description": "A new story",
            "genres": [Genre.objects.get(name="Drama").id],
            "actors": [actor.id],
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "New Play")
        self.assertEqual(response.data["description"], "A new story")

        play = Play.objects.get(title="New Play")
        self.assertIsNotNone(play)
        self.assertEqual(play.genres.count(), 1)
        self.assertEqual(play.actors.count(), 1)

    def test_play_upload_image_authenticated(self):
        """Test that an authenticated admin
         user can upload an image for a play."""
        url = f"/api/theatre/plays/{self.play.id}/upload-image/"
        actor = Actor.objects.get(first_name="John", last_name="Doe")
        img = Image.new("RGB", (10, 10))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG")
        img_byte_arr = img_byte_arr.getvalue()
        image = SimpleUploadedFile(
            "test_image.jpg", img_byte_arr, content_type="image/jpeg"
        )
        data = {
            "image": image,
            "description": "A new story",
            "title": "New Play",
            "genres": [Genre.objects.get(name="Drama").id],
            "actors": actor.id,
        }
        response = self.client.post(url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("image", response.data)
        self.play.refresh_from_db()
        self.assertIsNotNone(self.play.image)
        self.assertTrue(os.path.exists(self.play.image.path))
