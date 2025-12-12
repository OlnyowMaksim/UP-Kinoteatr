from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.spa_view, name='spa'),

    # API
    path('api/movies/', views.api_movies, name='api_movies'),
    path('api/user/', views.api_user, name='api_user'),
    path('api/booking/', views.api_booking, name='api_booking'),

    # Admin film management
    path('api/admin/movie/', views.api_admin_movie, name='api_admin_movie'),                # POST
    path('api/admin/movie/<int:movie_id>/', views.admin_movie_delete, name='admin_movie_delete'),  # DELETE

    path('profile/', views.home_redirect, name='profile_redirect'),
]
