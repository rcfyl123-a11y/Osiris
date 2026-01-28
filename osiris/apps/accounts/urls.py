"""osiris.apps.accounts.urls — маршруты для приложения accounts."""

from django.contrib.auth import views as auth_views
from django.urls import include, path

from . import forms, views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path(
        "login/",
        auth_views.LoginView.as_view(authentication_form=forms.LoginForm),
        name="login",
    ),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            form_class=forms.PasswordResetRequestForm
        ),
        name="password_reset",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            form_class=forms.SetPasswordFormStyled
        ),
        name="password_reset_confirm",
    ),
    path("", include("django.contrib.auth.urls")),
]
