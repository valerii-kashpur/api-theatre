from django.db import models

from user.models import User


class Play(models.Model):
    title = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField()
    genres = models.ManyToManyField('Genre', related_name='plays')
    actors = models.ManyToManyField('Actor', related_name='plays')

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']


class Genre(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return self.name


class Actor(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class TheatreHall(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    rows = models.PositiveIntegerField()
    seats_in_row = models.PositiveIntegerField()

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self):
        return self.name


class Performance(models.Model):
    play = models.ForeignKey(Play, on_delete=models.CASCADE)
    theatre_hall = models.ForeignKey(TheatreHall, on_delete=models.CASCADE)
    show_time = models.DateTimeField()

    def __str__(self):
        return f"{self.play} {self.theatre_hall}"

    class Meta:
        ordering = ['-show_time', 'theatre_hall']


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.created_at)

    class Meta:
        ordering = ['-created_at']


class Ticket(models.Model):
    row = models.PositiveIntegerField()
    seat = models.PositiveIntegerField()
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)

    def __str__(self):
        return f"{str(self.performance)} (row: {self.row}, seat: {self.seat})"

    class Meta:
        unique_together = ('row', 'seat', "performance")
        ordering = ['row', 'seat']
