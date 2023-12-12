from datetime import datetime

from django.db.models import F, Count
from rest_framework import mixins, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import GenericViewSet

from planetarium.models import (
    ShowTheme,
    PlanetariumDome,
    ShowSession,
    Reservation, AstronomyShow
)
from planetarium.serializers import (
    ShowThemeSerializer,
    PlanetariumDomeSerializer,
    AstronomyShowSerializer,
    AstronomyShowListSerializer,
    AstronomyShowDetailSerializer,
    ShowSessionSerializer,
    ReservationSerializer,
    ReservationListSerializer
)


class ShowThemeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = ShowTheme.objects.all()
    serializer_class = ShowThemeSerializer


class PlanetariumDomeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = PlanetariumDome.objects.all()
    serializer_class = PlanetariumDomeSerializer


class AstronomyShowViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    queryset = AstronomyShow.objects.prefetch_related("themes")
    serializer_class = AstronomyShowSerializer

    @staticmethod
    def _params_to_ints(queryset):
        return [int(str_id) for str_id in queryset.split(",")]

    def get_queryset(self):
        title = self.request.query_params.get("title", None)
        show_themes = self.request.query_params.get("show_themes")

        queryset = self.queryset
        if title:
            queryset = queryset.filter(title__icontains=title)
        if show_themes:
            show_themes_ids = self._params_to_ints(show_themes)
            queryset = queryset.filter(show_themes_id__in=show_themes_ids)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return AstronomyShowListSerializer

        if self.action == "retrieve":
            return AstronomyShowDetailSerializer

        return AstronomyShowSerializer


class ShowSessionViewSet(viewsets.ModelViewSet):
    queryset = (
        ShowSession.objects.all()
        .select_related("astronomy_show", "planetarium_dome")
        .annotate(
            tickets_available=(
                    F("planetarium_dome__rows") * F("planetarium_dome__seats_in_row")
                    - Count("tickets")
            )
        )
    )
    serializer_class = ShowSessionSerializer

    def get_queryset(self):
        date = self.request.query_params.get("date")
        astronomy_show_id = self.request.query_params.get("astronomy_show")

        queryset = self.queryset

        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(show__date=date)

        if astronomy_show_id:
            queryset = queryset.filter(astronomy_show_id=int(astronomy_show_id))

    def get_serializer_class(self):
        if self.action == "list":
            return AstronomyShowListSerializer

        if self.action == "retrieve":
            return AstronomyShowDetailSerializer

        return ShowSessionSerializer


class ReservationPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class ReservationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet
):
    queryset = Reservation.objects.prefetch_related(
        "tickets__show_session__astronomy_show",
        "tickets__show_session__planetarium_dome"
    )

    serializer_class = ReservationSerializer
    pagination_class = ReservationPagination

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer

        return ReservationSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

