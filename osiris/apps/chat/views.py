"""osiris.apps.chat.views — представления для приложения чатов."""

from __future__ import annotations

from django.db.models import Count, Max, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import ChatRoom


ROOM_TYPE_OPTIONS = {
    "all": "Все",
    "group": "Групповые",
    "direct": "Личные",
}


def room_list(request: HttpRequest) -> HttpResponse:
    """Показать список доступных комнат чата."""
    query = request.GET.get("q", "").strip()
    room_type = request.GET.get("type", "all")
    show_archived = request.GET.get("archived") == "1"

    rooms = (
        ChatRoom.objects.select_related("org", "created_by")
        .annotate(
            members_count=Count("memberships", distinct=True),
            last_message_at=Max("messages__sent_at"),
        )
        .order_by("-last_message_at", "-created_at")
    )

    if room_type in {"group", "direct"}:
        rooms = rooms.filter(room_type=room_type)

    if not show_archived:
        rooms = rooms.filter(is_archived=False)

    if query:
        rooms = rooms.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(org__name__icontains=query)
            | Q(org__full_name__icontains=query)
            | Q(direct_key__icontains=query)
        )

    context = {
        "query": query,
        "room_type": room_type,
        "room_type_options": ROOM_TYPE_OPTIONS,
        "show_archived": show_archived,
        "rooms": rooms,
    }
    return render(request, "chat/room_list.html", context)


def room_detail(request: HttpRequest, room_id: int) -> HttpResponse:
    """Показать информацию о конкретной комнате и последних сообщениях."""
    room = get_object_or_404(
        ChatRoom.objects.select_related("org", "created_by"),
        pk=room_id,
    )
    memberships = room.memberships.select_related("user").order_by(
        "user__last_name",
        "user__first_name",
        "user__username",
    )
    recent_messages_qs = (
        room.messages.select_related("sender", "reply_to")
        .prefetch_related("attachments")
        .filter(is_deleted=False)
        .order_by("-sent_at")[:50]
    )
    recent_messages = list(recent_messages_qs)[::-1]

    context = {
        "room": room,
        "memberships": memberships,
        "messages": recent_messages,
    }
    return render(request, "chat/room_detail.html", context)
