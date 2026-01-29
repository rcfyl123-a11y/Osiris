"""Сервисы и хелперы чата."""
from __future__ import annotations

from django.core.exceptions import PermissionDenied

from .models import ChatMembership, ChatRoom


def require_room_member(room, user) -> ChatMembership:
    membership = ChatMembership.objects.filter(
        room=room,
        user=user,
        left_at__isnull=True,
    ).first()
    if not membership:
        raise PermissionDenied("Нет доступа к комнате.")
    return membership


def get_user_rooms(user):
    return ChatRoom.objects.filter(
        memberships__user=user,
        memberships__left_at__isnull=True,
    ).distinct()


def is_room_admin(membership: ChatMembership) -> bool:
    return membership.role in {ChatMembership.Role.OWNER, ChatMembership.Role.ADMIN}


def can_manage_message(membership: ChatMembership, message) -> bool:
    return is_room_admin(membership) or message.sender_id == membership.user_id


def can_manage_members(membership: ChatMembership) -> bool:
    return is_room_admin(membership)
