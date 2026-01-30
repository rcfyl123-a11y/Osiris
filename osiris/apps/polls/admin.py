from django.contrib import admin
from django.utils import timezone

from .models import Choice, Poll, Question, Vote, VoteAnswer, Workplace


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Workplace)
class WorkplaceAdmin(admin.ModelAdmin):
    list_display = ("ip_address", "label", "department", "is_active")
    list_filter = ("is_active", "department")
    search_fields = ("ip_address", "label", "department")


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "status",
        "start_at",
        "end_at",
        "vote_count",
        "turnout_summary",
    )
    list_filter = ("status", "identity_mode", "vote_policy", "show_results_to_users")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("audience_workplaces",)
    inlines = (QuestionInline,)
    actions = ("publish_polls", "close_polls")

    @admin.display(description="Голосов")
    def vote_count(self, obj: Poll) -> int:
        return obj.votes.count()

    @admin.display(description="Явка")
    def turnout_summary(self, obj: Poll) -> str:
        eligible = obj.audience_queryset().count()
        voted = obj.votes.values("voter_ip").distinct().count()
        return f"{voted}/{eligible}"

    @admin.action(description="Опубликовать выбранные голосования")
    def publish_polls(self, request, queryset):
        for poll in queryset:
            poll.status = Poll.Status.PUBLISHED
            if not poll.start_at:
                poll.start_at = timezone.now()
            poll.save(update_fields=["status", "start_at", "updated_at"])
            self.log_change(request, poll, "Статус изменён на Published")

    @admin.action(description="Закрыть выбранные голосования")
    def close_polls(self, request, queryset):
        for poll in queryset:
            poll.status = Poll.Status.CLOSED
            if not poll.end_at:
                poll.end_at = timezone.now()
            poll.save(update_fields=["status", "end_at", "updated_at"])
            self.log_change(request, poll, "Статус изменён на Closed")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "poll", "type", "required", "order")
    list_filter = ("poll", "type", "required")
    search_fields = ("text",)
    inlines = (ChoiceInline,)


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("text", "question", "order")
    list_filter = ("question",)
    search_fields = ("text",)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("poll", "voter_ip", "workplace", "full_name", "created_at")
    list_filter = ("poll", "created_at")
    search_fields = ("voter_ip", "full_name", "workplace__label")


@admin.register(VoteAnswer)
class VoteAnswerAdmin(admin.ModelAdmin):
    list_display = ("vote", "question", "choice", "answer_text")
    list_filter = ("question",)
    search_fields = ("answer_text",)
