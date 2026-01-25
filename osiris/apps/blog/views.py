from django.shortcuts import render


NAVBAR_MESSAGE = "Welcome to the Blog App!"


def index(request):
    return render(request, "blog/index.html", {"navbar_message": NAVBAR_MESSAGE})
