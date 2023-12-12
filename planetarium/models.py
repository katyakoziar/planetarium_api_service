from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ShowTheme(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class PlanetariumDome(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self):
        return self.name


class AstronomyShow(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    themes = models.ManyToManyField(
        ShowTheme,
        related_name="astronomy_shows",
        blank=True
    )

    class Meta:
        ordering = ("title",)
        verbose_name = "astronomy_shows"
        verbose_name_plural = "astronomy_shows"

    def __str__(self):
        return self.title


class ShowSession(models.Model):
    astronomy_show = models.ForeignKey(
        AstronomyShow,
        on_delete=models.CASCADE,
        related_name="show_sessions"
    )
    planetarium_dome = models.ForeignKey(
        PlanetariumDome,
        on_delete=models.CASCADE,
        related_name="show_sessions"
    )
    show_time = models.DateTimeField()

    class Meta:
        ordering = ["-show_time"]

    def __str__(self):
        return self.astronomy_show.title + " " + str(self.show_time)


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return str(self.created_at)

    class Meta:
        ordering = ["-created_at"]


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    show_session = models.ForeignKey(
        ShowSession,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    def clean(self):
        if self.row < 1 or self.row > self.show_session.planetarium_dome.rows:
            raise ValidationError(
                {"row": "Row number must be within the range of rows in the planetarium dome."}
            )

        # Check if the seat is within the range
        if self.seat < 1 or self.seat > self.show_session.planetarium_dome.seats_in_row:
            raise ValidationError(
                {"seat": "Seat number must be within the range of seats in the row."}
            )

        if Ticket.objects.filter(
                show_session=self.show_session,
                row=self.row,
                seat=self.seat
        ).exclude(id=self.id).exists():
            raise ValidationError("This seat is already taken.")

    class Meta:
        unique_together = ("show_session", "row", "seat")
        ordering = ["row", "seat"]

    def __str__(self):
        return (
            f"{str(self.show_session)} (row: {self.row}, seat: {self.seat})"
        )
