from django.test import TestCase

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from django.urls import reverse

from planetarium.models import (
    AstronomyShow,
    ShowTheme,
    PlanetariumDome,
    ShowSession
)
from planetarium.serializers import (
    AstronomyShowListSerializer,
    AstronomyShowDetailSerializer
)

ASTRONOMY_SHOW_URL = reverse("planetarium:astronomyshow-list")
SHOW_SESSION_URL = reverse("planetarium:showsession-list")


def sample_astronomy_show(**params):
    defaults = {
        "title": "Test Astronomy Show",
        "description": "Test description",
    }
    defaults.update(params)
    return AstronomyShow.objects.create(**defaults)


def sample_show_theme(**params):
    defaults = {
        "name": "Test Theme"
    }
    defaults.update(params)
    return ShowTheme.objects.create(**defaults)


def sample_show_session(**params):
    planetarium_dome = PlanetariumDome.objects.create(
        name="Test Planetarium Dome",
        rows=20,
        seats_in_row=20
    )
    defaults = {
        "show_time": "2022-06-02 14:00:00",
        "astronomy_show": None,
        "planetarium_dome": planetarium_dome
    }
    defaults.update(params)
    return ShowSession.objects.create(**defaults)


def detail_astronomy_show_url(**params):
    return reverse(
        "planetarium:astronomyshow-detail",
        args=[params["astronomy_show_id"]]
    )


class UnauthenticatedPlanetariumApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(ASTRONOMY_SHOW_URL)
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )


class AuthenticatedPlanetariumApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpassword",
        )
        self.client.force_authenticate(self.user)

    def test_list_astronomy_shows(self):
        sample_astronomy_show(title="Show 1")
        astronomy_show_with_themes = sample_astronomy_show(title="Show 2")

        genre1 = sample_show_theme()
        genre2 = sample_show_theme(name="Test theme")
        astronomy_show_with_themes.themes.add(genre1, genre2)

        response = self.client.get(ASTRONOMY_SHOW_URL)

        astronomy_shows = AstronomyShow.objects.all()
        serializer = AstronomyShowListSerializer(astronomy_shows, many=True)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.data,
            serializer.data
        )

    def test_filter_astronomy_show_by_theme(self):
        astronomy_show1 = sample_astronomy_show(title="Show 1")
        astronomy_show2 = sample_astronomy_show(title="Show 2")
        astronomy_show3 = sample_astronomy_show(title="Show 3")
        theme1 = sample_show_theme()
        theme2 = sample_show_theme(name="Test theme")

        astronomy_show1.themes.add(theme1)
        astronomy_show2.themes.add(theme2)

        response = self.client.get(
            ASTRONOMY_SHOW_URL,
            {"show_themes": f"{theme1.id},{theme2.id}"}
        )

        serializer1 = AstronomyShowListSerializer(astronomy_show1)
        serializer2 = AstronomyShowListSerializer(astronomy_show2)
        serializer3 = AstronomyShowListSerializer(astronomy_show3)

        self.assertIn(serializer1.data, response.data)
        self.assertIn(serializer2.data, response.data)
        self.assertNotIn(serializer3.data, response.data)

    def test_retrieve_movies(self):
        astronomy_show = sample_astronomy_show()
        theme = sample_show_theme()
        astronomy_show.themes.add(theme)

        url = detail_astronomy_show_url(astronomy_show_id=astronomy_show.id)
        response = self.client.get(url)
        serializer = AstronomyShowDetailSerializer(astronomy_show)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_astronomy_show_forbidden(self):
        payload = {
            "title": "Sample astronomy show",
            "description": "Sample description",
        }

        response = self.client.post(ASTRONOMY_SHOW_URL, payload)
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )


class AdminPlanetariumApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@test.com",
            "adminpassword",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_astronomy_show(self):
        payload = {
            "title": "Sample astronomy show",
            "description": "Sample description",
        }
        response = self.client.post(ASTRONOMY_SHOW_URL, payload)
        show = AstronomyShow.objects.get(id=response.data["id"])

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        for key in payload:
            self.assertEqual(payload[key], getattr(show, key))

    def test_create_movie_with_genres(self):
        theme1 = sample_show_theme()
        theme2 = sample_show_theme(name="Test theme")
        payload = {
            "title": "Sample astronomy show",
            "description": "Sample description",
            "themes": [theme1.id, theme2.id]
        }
        response = self.client.post(ASTRONOMY_SHOW_URL, payload)
        astronomy_show = AstronomyShow.objects.get(id=response.data["id"])
        themes = astronomy_show.themes.all()

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertEqual(themes.count(), 2)
        self.assertIn(theme1, themes)
        self.assertIn(theme2, themes)

    def test_delete_astronomy_show_not_allowed(self):
        astronomy_show = sample_astronomy_show()
        url = detail_astronomy_show_url(astronomy_show_id=astronomy_show.id)
        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )
