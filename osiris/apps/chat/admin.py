"""Админ-настройки для приложения чатов."""

from django.contrib import admin

from . import models


@admin.register(models.ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "room_type", "name", "org", "is_archived", "created_at")
    list_filter = ("room_type", "is_archived")
    search_fields = ("name", "direct_key")


@admin.register(models.ChatMembership)
class ChatMembershipAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "user", "role", "joined_at", "left_at")
    list_filter = ("role",)
    search_fields = ("room__name", "user__username")


@admin.register(models.ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "sender", "sent_at", "is_deleted")
    list_filter = ("is_deleted", "body_format")
    search_fields = ("room__name", "sender__username", "body")


@admin.register(models.ChatAttachment)
class ChatAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "original_name", "size", "is_image", "uploaded_at")
    list_filter = ("is_image",)
    search_fields = ("original_name", "file")
