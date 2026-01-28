"""osiris.apps.accounts.views — представления регистрации и аутентификации."""

from django.contrib.auth import login
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .forms import SignupForm


def signup(request: HttpRequest) -> HttpResponse:
    """Зарегистрировать пользователя и выполнить вход после успешной регистрации."""
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = SignupForm()

    return render(request, "registration/signup.html", {"form": form})
