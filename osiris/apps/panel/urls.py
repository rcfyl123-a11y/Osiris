"""URL конфигурация панели управления."""

from django.urls import path

from . import views

app_name = "panel"

urlpatterns = [
    path("", views.PanelDashboardView.as_view(), name="dashboard"),
    path("core/ip-records/", views.PanelIPRecordListView.as_view(), name="ip_records"),
    path("core/denied/", views.PanelDeniedListView.as_view(), name="denied"),
    path("core/status/", views.PanelStatusView.as_view(), name="status"),
    path("core/apps/", views.PanelAppInventoryView.as_view(), name="app_inventory"),
    path("core/users/", views.PanelUsersView.as_view(), name="users"),
]
