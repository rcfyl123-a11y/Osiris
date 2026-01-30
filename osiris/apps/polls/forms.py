"""Формы для голосований."""

from django import forms

from .models import Choice, Poll, Question, Workplace


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


class PollCreateForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = (
            "title",
            "description",
            "status",
            "start_at",
            "end_at",
            "identity_mode",
            "vote_policy",
            "show_results_to_users",
            "audience_all",
            "audience_workplaces",
        )
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "start_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "end_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "identity_mode": forms.Select(attrs={"class": "form-select"}),
            "vote_policy": forms.Select(attrs={"class": "form-select"}),
            "show_results_to_users": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "audience_all": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "audience_workplaces": forms.SelectMultiple(attrs={"class": "form-select", "size": 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["audience_workplaces"].queryset = Workplace.objects.filter(is_active=True)
        self.fields["audience_workplaces"].required = False

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("audience_all"):
            cleaned_data["audience_workplaces"] = Workplace.objects.none()
        return cleaned_data

    def save(self, commit=True):
        poll = super().save(commit=commit)
        if poll.audience_all and commit:
            poll.audience_workplaces.clear()
        return poll
