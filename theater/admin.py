from django.contrib import admin
from .models import Genre, Movie, Hall, Session, Booking

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

class SessionInline(admin.TabularInline):
    model = Session
    extra = 1
    fields = ('hall', 'start_time', 'price')


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title','genre','duration_minutes','poster_url')
    list_filter = ('genre',)
    search_fields = ('title',)
    inlines = [SessionInline]

@admin.register(Hall)
class HallAdmin(admin.ModelAdmin):
    list_display = ('name', 'rows', 'seats_per_row')

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('movie','hall','start_time','price')
    list_filter = ('hall','start_time')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id','user','session','quantity','total_price','created_at')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
