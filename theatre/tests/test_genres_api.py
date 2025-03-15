from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from theatre.models import Genre
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class GenresViewSetUnauthenticatedTests(APITestCase):
    """Tests for GenresViewSet with an unauthenticated user."""

    def setUp(self):
        self.client = APIClient()
        Genre.objects.create(name="Drama")

    def test_genres_list_unauthenticated(self):
        """Test that an unauthenticated user cannot list genres."""
        url = "/api/theatre/genres/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided.",
        )

    def test_genres_create_unauthenticated(self):
        """Test that an unauthenticated user cannot create a genre."""
        url = "/api/theatre/genres/"
        data = {"name": "New Genre"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided.",
        )
        self.assertEqual(
            Genre.objects.count(), 1
        )  # Ensure no new genre was created


class GenresViewSetAuthenticatedAdminTests(APITestCase):
    """Tests for GenresViewSet with an authenticated admin user."""

    def setUp(self):
        self.user = User.objects.create_superuser(
            email="admin@example.com", password="adminpass123"
        )

        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        Genre.objects.create(name="Drama")

    def test_genres_list_authenticated(self):
        """Test that an authenticated admin user can list genres."""
        url = "/api/theatre/genres/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Drama")

    def test_genres_create_authenticated(self):
        """Test that an authenticated admin user can create a genre."""
        url = "/api/theatre/genres/"
        data = {"name": "Test Genre"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Test Genre")

        genre = Genre.objects.get(name="Test Genre")
        self.assertIsNotNone(genre)

    def test_genres_create_authenticated_duplicate(self):
        """Test that creating a duplicate genre returns a 400 error."""
        url = "/api/theatre/genres/"
        data = {"name": "Drama"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
        self.assertEqual(Genre.objects.count(), 1)


class GenresViewSetAuthenticatedUserTests(APITestCase):
    """Tests for GenresViewSet with an authenticated non-admin user."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="userpass123"
        )

        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        Genre.objects.all().delete()
        Genre.objects.create(name="Drama")

    def test_genres_list_authenticated(self):
        """Test that an authenticated non-admin user can list genres."""
        url = "/api/theatre/genres/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Drama")

    def test_genres_create_authenticated(self):
        """Test that an authenticated non-admin
         user cannot create a genre (returns 403 Forbidden)."""
        url = "/api/theatre/genres/"
        data = {"name": "Test Genre"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action.",
        )
        self.assertEqual(Genre.objects.count(), 1)
