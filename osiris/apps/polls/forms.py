"""Формы для голосований."""

from django import forms

from .models import Choice, Poll, Question


class PollVoteForm(forms.Form):
    def __init__(self, *args, poll: Poll, **kwargs):
        super().__init__(*args, **kwargs)
        self.poll = poll

        if poll.identity_mode == Poll.IdentityMode.NAME_REQUIRED:
            self.fields["full_name"] = forms.CharField(
                label="ФИО",
                max_length=255,
                required=True,
                widget=forms.TextInput(attrs={"class": "form-control"}),
            )

        questions = poll.questions.all().order_by("order", "id").prefetch_related("choices")
        for question in questions:
            field_name = f"question_{question.pk}"
            common_kwargs = {
                "label": question.text,
                "help_text": question.help_text,
                "required": question.required,
            }

            if question.type == Question.QuestionType.TEXT:
                self.fields[field_name] = forms.CharField(
                    **common_kwargs,
                    widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
                )
            elif question.type == Question.QuestionType.MULTI_CHOICE:
                self.fields[field_name] = forms.ModelMultipleChoiceField(
                    **common_kwargs,
                    queryset=Choice.objects.filter(question=question),
                    widget=forms.CheckboxSelectMultiple,
                )
            elif question.type == Question.QuestionType.SELECT:
                self.fields[field_name] = forms.ModelChoiceField(
                    **common_kwargs,
                    queryset=Choice.objects.filter(question=question),
                    widget=forms.Select(attrs={"class": "form-select"}),
                )
            else:
                self.fields[field_name] = forms.ModelChoiceField(
                    **common_kwargs,
                    queryset=Choice.objects.filter(question=question),
                    widget=forms.RadioSelect,
                )
