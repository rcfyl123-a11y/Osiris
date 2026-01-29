from __future__ import annotations

import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import ChatMembership, ChatMessage, ChatRoom


class ChatRoomTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user1 = self.user_model.objects.create_user(username="user1", password="pass123")
        self.user2 = self.user_model.objects.create_user(username="user2", password="pass123")
        self.user3 = self.user_model.objects.create_user(username="user3", password="pass123")
        self.client = Client()

    def _create_room(self, members):
        room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.GROUP, name="Test Room")
        for user in members:
            ChatMembership.objects.create(room=room, user=user, role=ChatMembership.Role.MEMBER)
        return room

    def test_room_access_control(self):
        room = self._create_room([self.user1])
        self.client.login(username="user2", password="pass123")
        response = self.client.get(reverse("chat:room_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, room.name)

        response = self.client.get(reverse("chat:room_detail", args=[room.id]))
        self.assertEqual(response.status_code, 403)

    def test_send_message_requires_membership(self):
        room = self._create_room([self.user1])
        self.client.login(username="user2", password="pass123")
        response = self.client.post(reverse("chat:send_message", args=[room.id]), {"body": "Привет"})
        self.assertEqual(response.status_code, 403)

    def test_direct_chat_dedup_by_direct_key(self):
        self.client.login(username="user1", password="pass123")
        response = self.client.post(
            reverse("chat:create_direct_chat"),
            {"user_id": self.user2.id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ChatRoom.objects.filter(room_type=ChatRoom.RoomType.DIRECT).count(), 1)

        response = self.client.post(
            reverse("chat:create_direct_chat"),
            {"user_id": self.user2.id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ChatRoom.objects.filter(room_type=ChatRoom.RoomType.DIRECT).count(), 1)

    def test_unread_count_logic(self):
        room = self._create_room([self.user1, self.user2])
        membership = ChatMembership.objects.get(room=room, user=self.user1)
        membership.last_read_at = timezone.now() - timezone.timedelta(hours=1)
        membership.save(update_fields=["last_read_at"])

        ChatMessage.objects.create(room=room, sender=self.user2, body="Новое сообщение")
        ChatMessage.objects.create(room=room, sender=self.user1, body="Ответ")

        self.client.login(username="user1", password="pass123")
        response = self.client.get(reverse("chat:room_list"))
        rooms = list(response.context["rooms"])
        room_data = next(room_item for room_item in rooms if room_item.id == room.id)
        self.assertEqual(room_data.unread_count, 1)

    @override_settings(CHAT_ALLOWED_CONTENT_TYPES=("text/plain",))
    def test_attachment_validation(self):
        room = self._create_room([self.user1])
        self.client.login(username="user1", password="pass123")
        bad_file = SimpleUploadedFile("malware.exe", b"boom", content_type="application/octet-stream")
        with tempfile.TemporaryDirectory() as tmp_dir:
            with override_settings(MEDIA_ROOT=tmp_dir):
                response = self.client.post(
                    reverse("chat:send_message", args=[room.id]),
                    {"body": "Файл", "attachments": bad_file},
                )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ChatMessage.objects.filter(room=room).count(), 0)
