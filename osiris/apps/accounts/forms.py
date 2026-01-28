"""osiris.apps.accounts.forms — формы для аутентификации и профиля."""

from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.contrib.auth.models import User


def _add_bootstrap_class(fields, class_name: str = "form-control") -> None:
    """Добавить bootstrap-класс к виджетам полей формы."""
    for field in fields.values():
        existing = field.widget.attrs.get("class", "")
        classes = existing.split() if existing else []
        if class_name not in classes:
            classes.append(class_name)
        field.widget.attrs["class"] = " ".join(classes)


class SignupForm(UserCreationForm):
    """Форма регистрации пользователя с bootstrap-стилями."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap_class(self.fields)


class LoginForm(AuthenticationForm):
    """Форма входа с локализованными подписями и bootstrap-стилями."""

    username = forms.CharField(
        label="Имя пользователя",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )


class PasswordResetRequestForm(PasswordResetForm):
    """Форма запроса сброса пароля с bootstrap-стилями."""

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )


class SetPasswordFormStyled(SetPasswordForm):
    """Форма установки нового пароля с bootstrap-стилями."""

    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    new_password2 = forms.CharField(
        label="Подтвердите пароль",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
