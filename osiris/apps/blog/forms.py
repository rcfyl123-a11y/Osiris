"""osiris.apps.blog.forms — формы для приложения блога."""

from django import forms

from .models import News


class NewsForm(forms.ModelForm):
    """Форма создания и редактирования новостей."""

    class Meta:
        model = News
        fields = ["title", "summary", "body", "image", "is_published"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "summary": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 8}),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
