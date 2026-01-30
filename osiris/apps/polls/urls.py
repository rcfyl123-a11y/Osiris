from django.urls import path

from . import views

app_name = "polls"

urlpatterns = [
    path("", views.poll_list, name="poll_list"),
    path("<slug:slug_or_id>/", views.poll_detail, name="poll_detail"),
    path("<int:poll_id>/thanks/", views.poll_thanks, name="poll_thanks"),
    path("<int:poll_id>/results/", views.poll_results, name="poll_results"),
    path("<int:poll_id>/results.csv", views.poll_results_csv, name="poll_results_csv"),
    path("<int:poll_id>/turnout/", views.poll_turnout, name="poll_turnout"),
    path("<int:poll_id>/turnout.csv", views.poll_turnout_csv, name="poll_turnout_csv"),
]
