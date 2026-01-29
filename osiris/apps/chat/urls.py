"""osiris.apps.chat.urls — маршруты для приложения чатов."""

from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("rooms/", views.room_list, name="room_list"),
    path("rooms/<int:room_id>/", views.room_detail, name="room_detail"),
]
