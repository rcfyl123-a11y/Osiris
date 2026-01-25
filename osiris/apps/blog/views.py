from django.shortcuts import get_object_or_404, redirect, render

from .forms import NewsForm
from .models import News


NAVBAR_MESSAGE = "Welcome to the Blog App!"


def home(request):
    return render(request, "blog/index.html", {"navbar_message": NAVBAR_MESSAGE})


def index(request):
    news_items = News.objects.filter(is_published=True)
    return render(
        request,
        "blog/news_list.html",
        {"news_items": news_items, "navbar_message": NAVBAR_MESSAGE},
    )


def detail(request, pk):
    news_item = get_object_or_404(News, pk=pk, is_published=True)
    return render(
        request,
        "blog/news_detail.html",
        {"news_item": news_item, "navbar_message": NAVBAR_MESSAGE},
    )


def create_news(request):
    if request.method == "POST":
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            news_item = form.save()
            return redirect("blog:detail", pk=news_item.pk)
    else:
        form = NewsForm()

    return render(
        request,
        "blog/news_form.html",
        {"form": form, "form_title": "Create news", "navbar_message": NAVBAR_MESSAGE},
    )


def edit_news(request, pk):
    news_item = get_object_or_404(News, pk=pk)

    if request.method == "POST":
        form = NewsForm(request.POST, request.FILES, instance=news_item)
        if form.is_valid():
            news_item = form.save()
            return redirect("blog:detail", pk=news_item.pk)
    else:
        form = NewsForm(instance=news_item)

    return render(
        request,
        "blog/news_form.html",
        {"form": form, "form_title": "Edit news", "navbar_message": NAVBAR_MESSAGE},
    )
