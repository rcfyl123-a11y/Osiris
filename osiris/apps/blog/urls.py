from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.index, name="index"),
    path("news/new/", views.create_news, name="create"),
    path("news/<int:pk>/", views.detail, name="detail"),
    path("news/<int:pk>/edit/", views.edit_news, name="edit"),
]
