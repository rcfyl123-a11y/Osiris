from django.contrib import messages


def toast_messages(request):
    return {"toast_messages": messages.get_messages(request)}
