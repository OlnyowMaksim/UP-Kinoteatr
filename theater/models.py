from django.db import models
from django.contrib.auth.models import User

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    def __str__(self): return self.name

class Movie(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=90)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, related_name='movies')
    poster_url = models.CharField(max_length=500, blank=True)
    def __str__(self): return self.title

class Hall(models.Model):
    name = models.CharField(max_length=100)
    rows = models.PositiveIntegerField(default=5)
    seats_per_row = models.PositiveIntegerField(default=10)
    def __str__(self): return self.name

class Session(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='sessions')
    hall = models.ForeignKey(Hall, on_delete=models.PROTECT)
    start_time = models.DateTimeField()
    price = models.DecimalField(max_digits=6, decimal_places=2, default=8.00)
    def __str__(self): return f"{self.movie.title} — {self.start_time}"

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Booking {self.id} — {self.user.username}"
