"""osiris.apps.blog.admin — настройки админки для блога."""

from django.contrib import admin

from .models import News


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    """Настройки отображения новостей в админке."""

    list_display = ("title", "is_published", "created_at")
    list_filter = ("is_published", "created_at")
    search_fields = ("title", "summary", "body")
    ordering = ("-created_at",)
