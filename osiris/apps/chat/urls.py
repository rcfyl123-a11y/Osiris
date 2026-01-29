"""osiris.apps.chat.urls — маршруты для приложения чатов."""

from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("rooms/", views.room_list, name="room_list"),
    path("rooms/<int:room_id>/", views.room_detail, name="room_detail"),
    path("rooms/<int:room_id>/send/", views.send_message, name="send_message"),
    path(
        "rooms/<int:room_id>/messages/<int:message_id>/edit/",
        views.edit_message,
        name="edit_message",
    ),
    path(
        "rooms/<int:room_id>/messages/<int:message_id>/delete/",
        views.delete_message,
        name="delete_message",
    ),
    path("rooms/<int:room_id>/members/add/", views.add_member, name="add_member"),
    path(
        "rooms/<int:room_id>/members/<int:user_id>/remove/",
        views.remove_member,
        name="remove_member",
    ),
    path("rooms/<int:room_id>/leave/", views.leave_room, name="leave_room"),
    path("rooms/<int:room_id>/archive/", views.toggle_archive, name="toggle_archive"),
    path("rooms/<int:room_id>/updates/", views.room_updates, name="room_updates"),
    path("direct/", views.create_direct_chat, name="create_direct_chat"),
    path("attachments/<int:attachment_id>/", views.attachment_download, name="attachment"),
    path(
        "attachments/<int:attachment_id>/preview/",
        views.attachment_preview,
        name="attachment_preview",
    ),
]
