"""URL routes for RCA views."""

from django.urls import path

from osiris.apps.rca import views

app_name = "rca"

urlpatterns = [
    path("orgs/", views.org_list, name="org_list"),
    path("orgs/<str:code>/", views.org_detail, name="org_detail"),
    path("posts/", views.post_list, name="post_list"),
    path("posts/<str:code>/", views.post_detail, name="post_detail"),
    path("employees/", views.employee_list, name="employee_list"),
    path("employees/<str:snils>/", views.employee_detail, name="employee_detail"),
]
