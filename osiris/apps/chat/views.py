"""osiris.apps.chat.views — представления для приложения чатов."""

from __future__ import annotations

from datetime import datetime
import mimetypes
from pathlib import Path
from urllib.parse import quote

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.db.models import Count, IntegerField, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import FileResponse, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.text import get_valid_filename

from .forms import ChatMemberAddForm, ChatMessageEditForm, ChatMessageForm, DirectChatForm
from .models import ChatAttachment, ChatMembership, ChatMessage, ChatRoom
from .services import (
    can_manage_members,
    can_manage_message,
    get_user_rooms,
    is_room_admin,
    require_room_member,
)


ROOM_TYPE_OPTIONS = {
    "all": "Все",
    "group": "Групповые",
    "direct": "Личные",
}


def _epoch() -> datetime:
    return datetime(1970, 1, 1, tzinfo=timezone.UTC)


def _build_unread_count_subquery(user):
    last_read_subquery = ChatMembership.objects.filter(
        room=OuterRef("pk"),
        user=user,
        left_at__isnull=True,
    ).values("last_read_at")[:1]

    unread_messages = (
        ChatMessage.objects.filter(
            room=OuterRef("pk"),
            is_deleted=False,
            sent_at__gt=Coalesce(Subquery(last_read_subquery), Value(_epoch())),
        )
        .exclude(sender=user)
        .values("room")
        .annotate(total=Count("id"))
        .values("total")
    )
    return Coalesce(Subquery(unread_messages), Value(0), output_field=IntegerField())


def _build_last_message_subquery():
    return (
        ChatMessage.objects.filter(room=OuterRef("pk"), is_deleted=False)
        .order_by("-sent_at")
        .values("sent_at", "body", "sender__username")[:1]
    )


def _build_content_disposition(disposition: str, filename: str) -> str:
    original_path = Path(filename or "")
    stem = get_valid_filename(original_path.stem) or "attachment"
    if original_path.suffix:
        safe_suffix = get_valid_filename(original_path.suffix).lstrip(".")
        safe_name = f"{stem}.{safe_suffix}" if safe_suffix else stem
    else:
        safe_name = stem
    ascii_fallback = safe_name.encode("ascii", "ignore").decode("ascii") or "attachment"
    quoted_name = quote(safe_name)
    return f"{disposition}; filename=\"{ascii_fallback}\"; filename*=UTF-8''{quoted_name}"


@login_required
def room_list(request: HttpRequest) -> HttpResponse:
    """Показать список доступных комнат чата."""
    query = request.GET.get("q", "").strip()
    room_type = request.GET.get("type", "all")
    show_archived = request.GET.get("archived") == "1"
    direct_form = DirectChatForm(current_user=request.user)

    rooms = get_user_rooms(request.user).select_related("org", "created_by")
    last_message = _build_last_message_subquery()
    rooms = rooms.annotate(
        members_count=Count(
            "memberships",
            filter=Q(memberships__left_at__isnull=True),
            distinct=True,
        ),
        last_message_at=Subquery(last_message.values("sent_at")[:1]),
        last_message_body=Subquery(last_message.values("body")[:1]),
        last_message_sender=Subquery(last_message.values("sender__username")[:1]),
        unread_count=_build_unread_count_subquery(request.user),
    ).order_by("-last_message_at", "-created_at")

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
        "direct_form": direct_form,
    }
    return render(request, "chat/room_list.html", context)


@login_required
def room_detail(request: HttpRequest, room_id: int) -> HttpResponse:
    """Показать информацию о конкретной комнате и последних сообщениях."""
    room = get_object_or_404(
        ChatRoom.objects.select_related("org", "created_by"),
        pk=room_id,
    )
    membership = require_room_member(room, request.user)
    memberships = room.memberships.filter(left_at__isnull=True).select_related("user").order_by(
        "user__last_name",
        "user__first_name",
        "user__username",
    )
    recent_messages_qs = (
        room.messages.select_related("sender", "reply_to")
        .prefetch_related("attachments")
        .order_by("-sent_at")[:50]
    )
    recent_messages = list(recent_messages_qs)[::-1]
    message_count = room.messages.count()
    message_form = ChatMessageForm()
    member_form = ChatMemberAddForm()
    last_message_at = recent_messages[-1].sent_at if recent_messages else None
    max_size_mb = settings.CHAT_ATTACHMENT_MAX_SIZE / (1024 * 1024)
    attachment_help = (
        f"Допустимые типы: {', '.join(settings.CHAT_ALLOWED_CONTENT_TYPES)}. "
        f"Максимум {max_size_mb:.0f} МБ."
    )

    ChatMembership.objects.filter(pk=membership.pk).update(last_read_at=timezone.now())

    context = {
        "room": room,
        "memberships": memberships,
        "messages": recent_messages,
        "message_count": message_count,
        "message_form": message_form,
        "member_form": member_form,
        "can_manage_members": can_manage_members(membership),
        "can_post": (not room.is_archived) or is_room_admin(membership),
        "is_room_admin": is_room_admin(membership),
        "membership": membership,
        "polling_interval": settings.CHAT_POLLING_INTERVAL_SECONDS,
        "last_message_at": last_message_at,
        "attachment_help": attachment_help,
    }
    return render(request, "chat/room_detail.html", context)


@login_required
def send_message(request: HttpRequest, room_id: int) -> HttpResponse:
    if request.method != "POST":
        return redirect("chat:room_detail", room_id=room_id)

    room = get_object_or_404(ChatRoom, pk=room_id)
    membership = require_room_member(room, request.user)
    if room.is_archived and not is_room_admin(membership):
        return redirect("chat:room_detail", room_id=room_id)

    def _render_with_form(form, status=400):
        memberships = room.memberships.select_related("user")
        recent_messages = (
            room.messages.select_related("sender", "reply_to")
            .prefetch_related("attachments")
            .order_by("-sent_at")[:50]
        )
        max_size_mb = settings.CHAT_ATTACHMENT_MAX_SIZE / (1024 * 1024)
        attachment_help = (
            f"Допустимые типы: {', '.join(settings.CHAT_ALLOWED_CONTENT_TYPES)}. "
            f"Максимум {max_size_mb:.0f} МБ."
        )
        context = {
            "room": room,
            "memberships": memberships,
            "messages": list(recent_messages)[::-1],
            "message_form": form,
            "member_form": ChatMemberAddForm(),
            "message_count": room.messages.count(),
            "can_manage_members": can_manage_members(membership),
            "can_post": (not room.is_archived) or is_room_admin(membership),
            "is_room_admin": is_room_admin(membership),
            "membership": membership,
            "polling_interval": settings.CHAT_POLLING_INTERVAL_SECONDS,
            "last_message_at": list(recent_messages)[-1].sent_at if recent_messages else None,
            "attachment_help": attachment_help,
        }
        return render(request, "chat/room_detail.html", context, status=status)

    form = ChatMessageForm(request.POST, request.FILES)
    if not form.is_valid():
        return _render_with_form(form)

    reply_to_id = form.cleaned_data.get("reply_to")
    reply_to = None
    if reply_to_id:
        reply_to = ChatMessage.objects.filter(room=room, pk=reply_to_id).first()
        if not reply_to:
            form.add_error("reply_to", "Сообщение для ответа не найдено.")

    if form.errors:
        return _render_with_form(form)

    message = ChatMessage.objects.create(
        room=room,
        sender=request.user,
        body=form.cleaned_data.get("body", "").strip(),
        reply_to=reply_to,
    )

    for file in form.cleaned_data.get("attachments", []):
        content_type = getattr(file, "content_type", "") or ""
        guessed_type, _ = mimetypes.guess_type(file.name)
        if not content_type or content_type == "application/octet-stream":
            content_type = guessed_type or content_type
        ChatAttachment.objects.create(
            message=message,
            file=file,
            content_type=content_type,
            original_name=file.name,
            size=file.size,
            is_image=bool(content_type and content_type.startswith("image/")),
        )

    return redirect(f"{reverse('chat:room_detail', args=[room_id])}#message-{message.id}")


@login_required
def edit_message(request: HttpRequest, room_id: int, message_id: int) -> HttpResponse:
    room = get_object_or_404(ChatRoom, pk=room_id)
    membership = require_room_member(room, request.user)
    message = get_object_or_404(ChatMessage, pk=message_id, room=room)
    if message.is_deleted or not can_manage_message(membership, message):
        raise PermissionDenied("Нет прав для редактирования сообщения.")

    if request.method == "POST":
        form = ChatMessageEditForm(request.POST, instance=message)
        if form.is_valid():
            form.save()
    return redirect(f"{reverse('chat:room_detail', args=[room_id])}#message-{message.id}")


@login_required
def delete_message(request: HttpRequest, room_id: int, message_id: int) -> HttpResponse:
    room = get_object_or_404(ChatRoom, pk=room_id)
    membership = require_room_member(room, request.user)
    message = get_object_or_404(ChatMessage, pk=message_id, room=room)
    if not can_manage_message(membership, message):
        raise PermissionDenied("Нет прав для удаления сообщения.")

    if request.method == "POST":
        if message.is_deleted:
            return redirect(f"{reverse('chat:room_detail', args=[room_id])}#message-{message.id}")
        message.body = "Сообщение удалено"
        message.is_deleted = True
        message.edited_at = timezone.now()
        message.save(update_fields=["body", "is_deleted", "edited_at"])
    return redirect(f"{reverse('chat:room_detail', args=[room_id])}#message-{message.id}")


@login_required
def attachment_download(request: HttpRequest, attachment_id: int) -> HttpResponse:
    attachment = get_object_or_404(
        ChatAttachment.objects.select_related("message__room"),
        pk=attachment_id,
    )
    room = attachment.message.room
    require_room_member(room, request.user)
    if attachment.message.is_deleted:
        raise PermissionDenied("Вложения удаленного сообщения недоступны.")

    file_handle = attachment.file.open("rb")
    response = FileResponse(file_handle, content_type=attachment.content_type or None)
    original = attachment.original_name or attachment.file.name
    response["Content-Length"] = attachment.size
    response["Content-Disposition"] = _build_content_disposition("attachment", original)
    return response


@login_required
def attachment_preview(request: HttpRequest, attachment_id: int) -> HttpResponse:
    attachment = get_object_or_404(
        ChatAttachment.objects.select_related("message__room"),
        pk=attachment_id,
    )
    room = attachment.message.room
    require_room_member(room, request.user)
    if attachment.message.is_deleted:
        raise PermissionDenied("Вложения удаленного сообщения недоступны.")
    if not attachment.is_image:
        return redirect("chat:attachment", attachment_id=attachment.id)

    file_handle = attachment.file.open("rb")
    response = FileResponse(file_handle, content_type=attachment.content_type or None)
    original = attachment.original_name or attachment.file.name
    response["Content-Length"] = attachment.size
    response["Content-Disposition"] = _build_content_disposition("inline", original)
    return response


@login_required
def create_direct_chat(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return redirect("chat:room_list")
    form = DirectChatForm(request.POST, current_user=request.user)
    if not form.is_valid():
        return redirect("chat:room_list")

    user_id = form.cleaned_data["user_id"]
    user_model = get_user_model()
    other_user = get_object_or_404(user_model, pk=user_id)
    direct_key = ChatRoom.build_direct_key([request.user.id, other_user.id])
    room, created = ChatRoom.objects.get_or_create(
        direct_key=direct_key,
        defaults={
            "room_type": ChatRoom.RoomType.DIRECT,
            "created_by": request.user,
        },
    )
    creator_membership, created_creator = ChatMembership.objects.get_or_create(
        room=room,
        user=request.user,
        defaults={"role": ChatMembership.Role.OWNER},
    )
    if not created_creator and creator_membership.left_at:
        creator_membership.left_at = None
        creator_membership.save(update_fields=["left_at"])
    other_membership, created_membership = ChatMembership.objects.get_or_create(
        room=room,
        user=other_user,
        defaults={"role": ChatMembership.Role.MEMBER},
    )
    if not created_membership and other_membership.left_at:
        other_membership.left_at = None
        other_membership.save(update_fields=["left_at"])
    return redirect("chat:room_detail", room_id=room.id)


@login_required
def add_member(request: HttpRequest, room_id: int) -> HttpResponse:
    room = get_object_or_404(ChatRoom, pk=room_id)
    membership = require_room_member(room, request.user)
    if room.room_type != ChatRoom.RoomType.GROUP or not can_manage_members(membership):
        raise PermissionDenied("Недостаточно прав для управления участниками.")
    if request.method == "POST":
        form = ChatMemberAddForm(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data["user_id"]
            user_model = get_user_model()
            user = get_object_or_404(user_model, pk=user_id)
            membership_obj, created = ChatMembership.objects.get_or_create(
                room=room,
                user=user,
                defaults={"role": ChatMembership.Role.MEMBER},
            )
            if not created and membership_obj.left_at:
                membership_obj.left_at = None
                membership_obj.save(update_fields=["left_at"])
    return redirect("chat:room_detail", room_id=room_id)


@login_required
def remove_member(request: HttpRequest, room_id: int, user_id: int) -> HttpResponse:
    room = get_object_or_404(ChatRoom, pk=room_id)
    membership = require_room_member(room, request.user)
    if room.room_type != ChatRoom.RoomType.GROUP or not can_manage_members(membership):
        raise PermissionDenied("Недостаточно прав для управления участниками.")
    if request.method == "POST":
        ChatMembership.objects.filter(room=room, user_id=user_id).update(left_at=timezone.now())
    return redirect("chat:room_detail", room_id=room_id)


@login_required
def leave_room(request: HttpRequest, room_id: int) -> HttpResponse:
    room = get_object_or_404(ChatRoom, pk=room_id)
    membership = require_room_member(room, request.user)
    if request.method == "POST":
        if membership.role == ChatMembership.Role.OWNER:
            has_other_owner = (
                ChatMembership.objects.filter(
                    room=room,
                    role=ChatMembership.Role.OWNER,
                    left_at__isnull=True,
                )
                .exclude(user=request.user)
                .exists()
            )
            if not has_other_owner:
                return redirect("chat:room_detail", room_id=room_id)
        membership.left_at = timezone.now()
        membership.save(update_fields=["left_at"])
    return redirect("chat:room_list")


@login_required
def toggle_archive(request: HttpRequest, room_id: int) -> HttpResponse:
    room = get_object_or_404(ChatRoom, pk=room_id)
    membership = require_room_member(room, request.user)
    if not can_manage_members(membership):
        raise PermissionDenied("Недостаточно прав для архивации.")
    if request.method == "POST":
        room.is_archived = not room.is_archived
        room.save(update_fields=["is_archived"])
    return redirect("chat:room_detail", room_id=room_id)


@login_required
def room_updates(request: HttpRequest, room_id: int) -> HttpResponse:
    room = get_object_or_404(ChatRoom, pk=room_id)
    require_room_member(room, request.user)
    after = request.GET.get("after")
    after_dt = parse_datetime(after) if after else None
    if after_dt and timezone.is_naive(after_dt):
        after_dt = timezone.make_aware(after_dt, timezone.get_current_timezone())
    messages_qs = room.messages.select_related("sender").prefetch_related("attachments")
    if after_dt:
        messages_qs = messages_qs.filter(sent_at__gt=after_dt)
    messages_qs = messages_qs.order_by("sent_at")[:50]

    payload = []
    for message in messages_qs:
        attachments = []
        if not message.is_deleted:
            attachments = [
                {
                    "id": attachment.id,
                    "name": attachment.original_name or attachment.file.name,
                    "is_image": attachment.is_image,
                }
                for attachment in message.attachments.all()
            ]
        payload.append(
            {
                "id": message.id,
                "body": message.body,
                "sent_at": message.sent_at.isoformat(),
                "sender": str(message.sender) if message.sender else "Система",
                "is_deleted": message.is_deleted,
                "attachments": attachments,
            }
        )
    return JsonResponse({"messages": payload})
