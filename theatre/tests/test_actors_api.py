from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from theatre.models import Actor
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class ActorViewSetUnauthenticatedTests(APITestCase):
    """Tests for ActorViewSet with an unauthenticated user."""

    def setUp(self):
        self.client = APIClient()
        Actor.objects.create(first_name="John", last_name="Doe")

    def test_actors_list_unauthenticated(self):
        """Test that an unauthenticated user cannot list actors (returns 401 Unauthorized)."""
        url = "/api/theatre/actors/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )

    def test_actors_create_unauthenticated(self):
        """Test that an unauthenticated user cannot create an actor."""
        url = "/api/theatre/actors/"
        data = {"first_name": "Jane", "last_name": "Smith"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )
        self.assertEqual(
            Actor.objects.count(),
            1
        )


class ActorViewSetAuthenticatedAdminTests(APITestCase):
    """Tests for ActorViewSet with an authenticated admin user."""

    def setUp(self):
        """Set up test data, admin user, and authenticated client."""
        # Create a test admin user
        self.user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

        # Initialize API client and set the Authorization header
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        # Clear existing actors and create only one for testing
        Actor.objects.all().delete()
        Actor.objects.create(first_name="John", last_name="Doe")

    def test_actors_list_authenticated(self):
        """Test that an authenticated admin user can list actors."""
        url = "/api/theatre/actors/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data["results"]),
            1
        )  # Check the number of actors in results
        self.assertEqual(response.data["results"][0]["full_name"], "John Doe")

    def test_actors_create_authenticated(self):
        """Test that an authenticated admin user can create an actor."""
        url = "/api/theatre/actors/"
        data = {"first_name": "Jane", "last_name": "Smith"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["full_name"], "Jane Smith")

        # Verify the actor exists in the database
        actor = Actor.objects.get(first_name="Jane", last_name="Smith")
        self.assertIsNotNone(actor)


class ActorViewSetAuthenticatedUserTests(APITestCase):
    """Tests for ActorViewSet with an authenticated non-admin user."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="userpass123"
        )

        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        Actor.objects.all().delete()
        Actor.objects.create(first_name="John", last_name="Doe")

    def test_actors_list_authenticated(self):
        """Test that an authenticated non-admin user can list actors."""
        url = "/api/theatre/actors/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data["results"]),
            1
        )
        self.assertEqual(response.data["results"][0]["full_name"], "John Doe")

    def test_actors_create_authenticated(self):
        """Test that an authenticated non-admin user cannot create an actor (returns 403 Forbidden)."""
        url = "/api/theatre/actors/"
        data = {"first_name": "Jane", "last_name": "Smith"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["detail"],
            "You do not have permission to perform this action."
        )
        self.assertEqual(
            Actor.objects.count(),
            1
        )
