"""osiris.apps.accounts.urls — маршруты для приложения accounts."""

from django.contrib.auth import views as auth_views
from django.urls import include, path

from . import forms, views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            authentication_form=forms.LoginForm,
            template_name="accounts/registration/login.html",
        ),
        name="login",
    ),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            form_class=forms.PasswordResetRequestForm,
            template_name="accounts/registration/password_reset_form.html",
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            form_class=forms.SetPasswordFormStyled,
            template_name="accounts/registration/password_reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("", include("django.contrib.auth.urls")),
]
