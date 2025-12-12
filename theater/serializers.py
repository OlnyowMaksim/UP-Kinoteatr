from rest_framework import serializers
from .models import Movie, Session, Booking, Hall, Genre

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['id', 'start_time', 'price']

class MovieSerializer(serializers.ModelSerializer):
    genre = GenreSerializer()
    sessions = SessionSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ['id', 'title', 'description', 'duration_minutes', 'genre', 'poster_url', 'sessions']

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'session', 'quantity', 'total_price', 'created_at']
