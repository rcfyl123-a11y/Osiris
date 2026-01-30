"""Представления для голосований."""

from __future__ import annotations

import csv

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import PollCreateForm, PollVoteForm
from .models import Poll, Question, Vote, VoteAnswer, Workplace
from .utils import get_client_ip


POLL_RESULT_COLORS = [
    "polls-color-emerald",
    "polls-color-blue",
    "polls-color-violet",
    "polls-color-amber",
    "polls-color-rose",
    "polls-color-teal",
]


def poll_list(request: HttpRequest) -> HttpResponse:
    polls = Poll.objects.exclude(status=Poll.Status.DRAFT).order_by("-start_at", "-created_at")
    return render(request, "polls/poll_list.html", {"polls": polls, "now": timezone.now()})


@staff_member_required
def poll_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = PollCreateForm(request.POST)
        if form.is_valid():
            poll = form.save()
            messages.success(request, "Голосование создано. Добавьте вопросы через админ-панель.")
            return redirect("polls:poll_list")
    else:
        form = PollCreateForm()

    return render(request, "polls/poll_create.html", {"form": form})


def _get_poll(slug_or_id: str) -> Poll:
    if slug_or_id.isdigit():
        return get_object_or_404(Poll, pk=int(slug_or_id))
    return get_object_or_404(Poll, slug=slug_or_id)


def poll_detail(request: HttpRequest, slug_or_id: str) -> HttpResponse:
    poll = _get_poll(slug_or_id)
    now = timezone.now()
    client_ip = get_client_ip(request)

    if not client_ip:
        return HttpResponseForbidden("Не удалось определить IP-адрес.")

    workplace = Workplace.objects.filter(ip_address=client_ip, is_active=True).first()
    eligible_workplaces = poll.audience_queryset()

    if not eligible_workplaces.filter(ip_address=client_ip).exists():
        return render(
            request,
            "polls/poll_unavailable.html",
            {
                "poll": poll,
                "status_message": "Ваше рабочее место не входит в аудиторию голосования.",
            },
            status=403,
        )

    if poll.status in {Poll.Status.DRAFT, Poll.Status.CLOSED, Poll.Status.ARCHIVED}:
        return render(
            request,
            "polls/poll_unavailable.html",
            {
                "poll": poll,
                "status_message": "Голосование недоступно.",
            },
            status=403,
        )

    if poll.start_at and now < poll.start_at:
        return render(
            request,
            "polls/poll_unavailable.html",
            {
                "poll": poll,
                "status_message": "Голосование ещё не началось.",
            },
        )

    if poll.end_at and now > poll.end_at:
        return render(
            request,
            "polls/poll_unavailable.html",
            {
                "poll": poll,
                "status_message": "Голосование завершено.",
                "show_results": _can_view_results(request, poll),
            },
        )

    existing_vote = Vote.objects.filter(poll=poll, voter_ip=client_ip).first()

    if existing_vote and poll.vote_policy == Poll.VotePolicy.SINGLE:
        return render(
            request,
            "polls/poll_unavailable.html",
            {
                "poll": poll,
                "status_message": "Вы уже голосовали. Повторное голосование недоступно.",
                "show_results": _can_view_results(request, poll),
            },
            status=403,
        )

    questions = poll.questions.all().order_by("order", "id").prefetch_related("choices")

    if request.method == "POST":
        form = PollVoteForm(request.POST, poll=poll)
        if form.is_valid():
            try:
                with transaction.atomic():
                    vote = _save_vote(
                        poll=poll,
                        form=form,
                        client_ip=client_ip,
                        workplace=workplace,
                        existing_vote=existing_vote,
                    )
                    _save_answers(vote, form)
            except IntegrityError:
                messages.error(request, "Не удалось сохранить голос. Попробуйте ещё раз.")
            else:
                messages.success(request, "Ваш голос учтён.")
                return redirect("polls:poll_thanks", poll_id=poll.pk)
    else:
        form = PollVoteForm(poll=poll)

    question_blocks = []
    for question in questions:
        field_name = f"question_{question.pk}"
        try:
            field = form[field_name]
        except KeyError:
            field = None
        question_blocks.append({"question": question, "field": field})

    return render(
        request,
        "polls/poll_detail.html",
        {
            "poll": poll,
            "form": form,
            "workplace": workplace,
            "questions": questions,
            "question_blocks": question_blocks,
            "show_missing_fields": settings.DEBUG or request.user.is_staff,
        },
    )


def _save_vote(
    *,
    poll: Poll,
    form: PollVoteForm,
    client_ip: str,
    workplace: Workplace | None,
    existing_vote: Vote | None,
) -> Vote:
    full_name = form.cleaned_data.get("full_name", "")

    if existing_vote and poll.vote_policy == Poll.VotePolicy.REVOTE_UNTIL_END and not poll.has_ended:
        existing_vote.full_name = full_name
        existing_vote.workplace = workplace
        existing_vote.save(update_fields=["full_name", "workplace", "updated_at"])
        existing_vote.answers.all().delete()
        return existing_vote

    return Vote.objects.create(
        poll=poll,
        voter_ip=client_ip,
        workplace=workplace,
        full_name=full_name,
    )


def _save_answers(vote: Vote, form: PollVoteForm) -> None:
    for question in vote.poll.questions.all():
        field_name = f"question_{question.pk}"
        value = form.cleaned_data.get(field_name)
        if value in (None, ""):
            continue
        if question.type == Question.QuestionType.TEXT:
            VoteAnswer.objects.create(vote=vote, question=question, answer_text=value)
        elif question.type == Question.QuestionType.MULTI_CHOICE:
            for choice in value:
                VoteAnswer.objects.create(vote=vote, question=question, choice=choice)
        else:
            VoteAnswer.objects.create(vote=vote, question=question, choice=value)


def poll_thanks(request: HttpRequest, poll_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, pk=poll_id)
    return render(request, "polls/poll_thanks.html", {"poll": poll})


def _can_view_results(request: HttpRequest, poll: Poll) -> bool:
    return request.user.is_staff or poll.show_results_to_users or poll.has_ended


def poll_results(request: HttpRequest, poll_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, pk=poll_id)
    if not _can_view_results(request, poll):
        return HttpResponseForbidden("Результаты недоступны.")

    result_blocks = []
    text_pages = {}

    for question in poll.questions.prefetch_related("choices"):
        answers_qs = VoteAnswer.objects.filter(question=question)
        total_votes = answers_qs.values("vote_id").distinct().count()

        if question.type == Question.QuestionType.TEXT:
            paginator = Paginator(answers_qs.exclude(answer_text=""), 20)
            page_number = request.GET.get(f"q{question.pk}_page", 1)
            text_pages[question.pk] = paginator.get_page(page_number)
            result_blocks.append(
                {
                    "question": question,
                    "total": total_votes,
                    "type": "text",
                }
            )
            continue

        choice_counts = (
            answers_qs.filter(choice__isnull=False)
            .values("choice")
            .annotate(total=Count("choice"))
        )
        count_map = {item["choice"]: item["total"] for item in choice_counts}

        choices_data = []
        for idx, choice in enumerate(question.choices.all()):
            count = count_map.get(choice.pk, 0)
            percent = (count / total_votes * 100) if total_votes else 0
            color_class = POLL_RESULT_COLORS[idx % len(POLL_RESULT_COLORS)]
            choices_data.append(
                {
                    "choice": choice,
                    "count": count,
                    "percent": percent,
                    "color_class": color_class,
                }
            )

        result_blocks.append(
            {
                "question": question,
                "total": total_votes,
                "choices": choices_data,
                "type": "choices",
            }
        )

    turnout = _build_turnout(poll)

    return render(
        request,
        "polls/poll_results.html",
        {
            "poll": poll,
            "result_blocks": result_blocks,
            "text_pages": text_pages,
            "turnout": turnout,
        },
    )


def poll_results_csv(request: HttpRequest, poll_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, pk=poll_id)
    if not _can_view_results(request, poll):
        return HttpResponseForbidden("Результаты недоступны.")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="poll_{poll_id}_results.csv"'

    writer = csv.writer(response)
    writer.writerow(["Голосование", poll.title])

    for question in poll.questions.prefetch_related("choices"):
        writer.writerow([])
        writer.writerow(["Вопрос", question.text])
        answers_qs = VoteAnswer.objects.filter(question=question)
        total_votes = answers_qs.values("vote_id").distinct().count()

        if question.type == Question.QuestionType.TEXT:
            writer.writerow(["Тип", "Текстовые ответы"])
            for answer in answers_qs.exclude(answer_text=""):
                writer.writerow([answer.answer_text])
            continue

        writer.writerow(["Всего ответов", total_votes])
        choice_counts = (
            answers_qs.filter(choice__isnull=False)
            .values("choice")
            .annotate(total=Count("choice"))
        )
        count_map = {item["choice"]: item["total"] for item in choice_counts}
        for choice in question.choices.all():
            count = count_map.get(choice.pk, 0)
            percent = (count / total_votes * 100) if total_votes else 0
            writer.writerow([choice.text, count, f"{percent:.2f}%"])

    return response


@staff_member_required
def poll_turnout(request: HttpRequest, poll_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, pk=poll_id)
    turnout = _build_turnout(poll)

    return render(
        request,
        "polls/poll_turnout.html",
        {
            "poll": poll,
            "turnout": turnout,
        },
    )


@staff_member_required
def poll_turnout_csv(request: HttpRequest, poll_id: int) -> HttpResponse:
    poll = get_object_or_404(Poll, pk=poll_id)
    turnout = _build_turnout(poll)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="poll_{poll_id}_turnout.csv"'

    writer = csv.writer(response)
    writer.writerow(["Голосование", poll.title])
    writer.writerow(["Всего аудитории", turnout["eligible_count"]])
    writer.writerow(["Проголосовали", turnout["voted_count"]])
    writer.writerow(["Не проголосовали", turnout["not_voted_count"]])

    writer.writerow([])
    writer.writerow(["Проголосовали (IP)"])
    for workplace in turnout["voted_workplaces"]:
        writer.writerow([workplace.ip_address, workplace.label, workplace.department])

    writer.writerow([])
    writer.writerow(["Не проголосовали (IP)"])
    for workplace in turnout["not_voted_workplaces"]:
        writer.writerow([workplace.ip_address, workplace.label, workplace.department])

    return response


def _build_turnout(poll: Poll) -> dict:
    eligible_workplaces = poll.audience_queryset()
    voted_ips = Vote.objects.filter(poll=poll).values_list("voter_ip", flat=True)
    voted_workplaces = eligible_workplaces.filter(ip_address__in=voted_ips)
    not_voted_workplaces = eligible_workplaces.exclude(ip_address__in=voted_ips)

    return {
        "eligible_count": eligible_workplaces.count(),
        "voted_count": voted_workplaces.count(),
        "not_voted_count": not_voted_workplaces.count(),
        "voted_workplaces": voted_workplaces,
        "not_voted_workplaces": not_voted_workplaces,
    }
