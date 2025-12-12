from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json
import datetime
from zoneinfo import ZoneInfo
from .models import Movie, Session, Hall
from django.utils import timezone
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .serializers import MovieSerializer, BookingSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework import status

@swagger_auto_schema(
    method='delete',
    manual_parameters=[
        openapi.Parameter(
            'movie_id',
            openapi.IN_PATH,
            description="ID фильма для удаления",
            type=openapi.TYPE_INTEGER,
            required=True
        )
    ],
    responses={200: "Удалено", 404: "Фильм не найден"},
    tags=['admin']
)
@api_view(['DELETE'])
def admin_movie_delete(request, movie_id):
    try:
        movie = Movie.objects.get(id=movie_id)
        movie.delete()
        return Response({"message": "Удалено"}, status=200)
    except Movie.DoesNotExist:
        return Response({"error": "Фильм не найден"}, status=404)
    
def spa_view(request):
    return render(request, 'theater/spa.html')

@swagger_auto_schema(
    method='get',
    tags=['Movies'],
    operation_description="Получить список фильмов",
    responses={200: MovieSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def api_movies(request):
    movies = Movie.objects.all().select_related('genre')
    serializer = MovieSerializer(movies, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    tags=['User'],
    operation_description="Получить профиль текущего пользователя",
    responses={200: openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING),
            'email': openapi.Schema(type=openapi.TYPE_STRING),
            'first_name': openapi.Schema(type=openapi.TYPE_STRING),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING),
            'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'bookings': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT))
        }
    )}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_user(request):
    if not request.user.is_authenticated:
        return HttpResponse(status=401)

    bookings = []
    msk = ZoneInfo('Europe/Moscow')
    for b in request.user.bookings.select_related('session__movie').order_by('-created_at'):
        local_dt = timezone.localtime(b.session.start_time, msk)
        bookings.append({
            'id': b.id,
            'movie': b.session.movie.title,
            'session_time': local_dt.strftime('%Y-%m-%d %H:%M'),
            'quantity': b.quantity,
            'total_price': float(b.total_price),
        })

    return JsonResponse({
        'username': request.user.username,
        'email': request.user.email,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'is_staff': request.user.is_staff,
        'bookings': bookings
    })

@swagger_auto_schema(
    method='post',
    tags=['Booking'],
    operation_description="Создать бронь",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'movie_title': openapi.Schema(type=openapi.TYPE_STRING),
            'seats': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
        },
        required=['movie_title']
    ),
    responses={200: BookingSerializer(), 500: 'Ошибка при создании бронирования'}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_booking(request):
    movie_title = request.data.get('movie_title') or 'Без названия'
    seats = request.data.get('seats', [])

    try:
        movie, _ = Movie.objects.get_or_create(title=movie_title, defaults={'description': '', 'duration_minutes': 90})
        hall, _ = Hall.objects.get_or_create(name='Основной', defaults={'rows': 5, 'seats_per_row': 10})
        session = Session.objects.filter(movie=movie).order_by('start_time').first()
        if not session:
            session = Session.objects.create(movie=movie, hall=hall, start_time=timezone.now(), price=400)
        quantity = max(1, len(seats))
        from .models import Booking
        from decimal import Decimal
        total_price = Decimal(str(session.price)) * quantity
        booking = Booking.objects.create(
            user=request.user, 
            session=session, 
            quantity=quantity, 
            total_price=total_price
        )
        return JsonResponse({'status': 'ok', 'booking_id': booking.id})
    except Exception as e:
        return JsonResponse({'error': 'Ошибка при создании бронирования', 'detail': str(e)}, status=500)

def home_redirect(request):
    return redirect('spa')

@swagger_auto_schema(
    method='post',
    tags=['Admin'],
    operation_description="Создать или обновить фильм",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'title': openapi.Schema(type=openapi.TYPE_STRING),
            'genre': openapi.Schema(type=openapi.TYPE_STRING),
            'times': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
            'poster_url': openapi.Schema(type=openapi.TYPE_STRING),
        },
        required=['title','genre','times']
    ),
    responses={200: MovieSerializer()}
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def api_admin_movie(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    if request.method not in ('POST', 'DELETE'):
        return HttpResponseBadRequest('POST or DELETE only')
    
    title = request.data.get('title')
    genre_name = request.data.get('genre')
    times = request.data.get('times', [])
    poster_url = request.data.get('poster_url') or ''

    if not title or not genre_name or not isinstance(times, list) or len(times) == 0:
        return HttpResponseBadRequest('title, genre, times required')

    genre_model = Movie._meta.get_field('genre').related_model
    genre, _ = genre_model.objects.get_or_create(name=genre_name, defaults={'slug': genre_name.lower().replace(' ','-')})
    movie, _ = Movie.objects.get_or_create(title=title, defaults={
        'genre': genre,
        'duration_minutes': 120,
        'poster_url': poster_url
    })
    movie.genre = genre
    if poster_url:
        movie.poster_url = poster_url
    movie.save()

    msk = ZoneInfo('Europe/Moscow')
    today_msk = timezone.now().astimezone(msk)
    hall, _ = Hall.objects.get_or_create(name='Основной', defaults={'rows': 5, 'seats_per_row': 10})
    created_sessions = []
    for t in times:
        try:
            h, m = map(int, t.split(':'))
        except Exception:
            continue
        start = datetime.datetime(today_msk.year, today_msk.month, today_msk.day, h, m, tzinfo=msk)
        sess, _ = Session.objects.get_or_create(movie=movie, hall=hall, start_time=start, defaults={'price': 400})
        created_sessions.append(sess.id)

    return JsonResponse({'status': 'ok', 'movie_id': movie.id, 'sessions': created_sessions})

def logout_view(request):
    """
    Явный logout с безопасным GET/POST и редиректом на страницу логина.
    """
    auth_logout(request)
    return redirect('login')

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('spa')

def logout_view(request):
    auth_logout(request)
    return redirect('login')



from django.contrib.auth import login as auth_login
from django.shortcuts import render
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.db import IntegrityError

def register(request):
    if request.user.is_authenticated:
        return redirect('spa')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
            except IntegrityError:
                form.add_error('username', 'Пользователь с таким логином уже существует.')
            else:
                auth_login(request, user)
                messages.success(request, 'Аккаунт создан и вы вошли в систему.')
                return redirect('spa')
        messages.error(request, 'Проверьте форму — есть ошибки.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})
