from django.urls import path

from . import views

app_name = "polls"

urlpatterns = [
    path("", views.poll_list, name="poll_list"),
    path("create/", views.poll_create, name="poll_create"),
    path("<int:poll_id>/builder/", views.poll_builder, name="poll_builder"),
    path(
        "<int:poll_id>/builder/questions/add/",
        views.poll_question_create,
        name="poll_question_create",
    ),
    path(
        "<int:poll_id>/builder/questions/<int:question_id>/",
        views.poll_question_edit,
        name="poll_question_edit",
    ),
    path(
        "<int:poll_id>/builder/questions/<int:question_id>/delete/",
        views.poll_question_delete,
        name="poll_question_delete",
    ),
    path("<slug:slug_or_id>/", views.poll_detail, name="poll_detail"),
    path("<int:poll_id>/thanks/", views.poll_thanks, name="poll_thanks"),
    path("<int:poll_id>/results/", views.poll_results, name="poll_results"),
    path("<int:poll_id>/results.csv", views.poll_results_csv, name="poll_results_csv"),
    path("<int:poll_id>/results.xlsx", views.poll_results_xlsx, name="poll_results_xlsx"),
    path("<int:poll_id>/results.xls", views.poll_results_xls, name="poll_results_xls"),
    path("<int:poll_id>/results/people/", views.poll_results_people, name="poll_results_people"),
    path(
        "<int:poll_id>/results/people/<int:vote_id>/",
        views.poll_results_person,
        name="poll_results_person",
    ),
    path(
        "<int:poll_id>/results/people.csv",
        views.poll_results_people_csv,
        name="poll_results_people_csv",
    ),
    path(
        "<int:poll_id>/results/people.xlsx",
        views.poll_results_people_xlsx,
        name="poll_results_people_xlsx",
    ),
    path(
        "<int:poll_id>/results/people.xls",
        views.poll_results_people_xls,
        name="poll_results_people_xls",
    ),
    path("<int:poll_id>/turnout/", views.poll_turnout, name="poll_turnout"),
    path("<int:poll_id>/turnout.csv", views.poll_turnout_csv, name="poll_turnout_csv"),
]
