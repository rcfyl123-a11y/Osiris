"""osiris.apps.blog.views — представления для приложения блога."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import NewsForm
from .models import News


NAVBAR_MESSAGE = "Добро пожаловать в приложение блога!"


def index(request: HttpRequest) -> HttpResponse:
    """Показать опубликованные новости."""
    news_items = News.objects.filter(is_published=True)
    return render(
        request,
        "blog/news_list.html",
        {"news_items": news_items, "navbar_message": NAVBAR_MESSAGE},
    )


def detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Показать опубликованную новость."""
    news_item = get_object_or_404(News, pk=pk, is_published=True)
    return render(
        request,
        "blog/news_detail.html",
        {"news_item": news_item, "navbar_message": NAVBAR_MESSAGE},
    )


def create_news(request: HttpRequest) -> HttpResponse:
    """Создать новость."""
    return _handle_news_form(request, form_title="Создать новость")


def edit_news(request: HttpRequest, pk: int) -> HttpResponse:
    """Отредактировать существующую новость."""
    news_item = get_object_or_404(News, pk=pk)
    return _handle_news_form(request, instance=news_item, form_title="Редактировать новость")


def _handle_news_form(
    request: HttpRequest, *, form_title: str, instance: News | None = None
) -> HttpResponse:
    """Обработать форму создания/редактирования новости."""
    if request.method == "POST":
        form = NewsForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            news_item = form.save()
            return redirect("blog:detail", pk=news_item.pk)
    else:
        form = NewsForm(instance=instance)

    return render(
        request,
        "blog/news_form.html",
        {"form": form, "form_title": form_title, "navbar_message": NAVBAR_MESSAGE},
    )
