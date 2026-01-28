"""osiris.apps.blog.models — модели данных для блога."""

from django.db import models


class News(models.Model):
    """Новостная запись, публикуемая в блоге."""

    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    body = models.TextField()
    image = models.ImageField(upload_to="news_images/", blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title
