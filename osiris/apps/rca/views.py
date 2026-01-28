"""Views for RCA employee/org/post browsing."""

from __future__ import annotations

from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from osiris.apps.rca.models import Employee, EmployeeSnapshot, Org, OrgVersion, Post, PostVersion


def org_list(request):
    query = request.GET.get("q", "").strip()
    show_history = request.GET.get("history") == "1"

    versions = OrgVersion.objects.select_related("org").order_by("org__code", "-valid_from")
    if not show_history:
        versions = versions.filter(is_current=True)
    if query:
        versions = versions.filter(
            Q(org__code__icontains=query)
            | Q(name__icontains=query)
            | Q(full_name__icontains=query)
            | Q(parent_code__icontains=query)
        )

    context = {
        "query": query,
        "show_history": show_history,
        "org_versions": versions,
    }
    return render(request, "rca/org_list.html", context)


def org_detail(request, code: str):
    org = get_object_or_404(Org, code=code)
    versions = org.versions.order_by("-valid_from")
    current = versions.filter(is_current=True).first()
    employees = (
        EmployeeSnapshot.objects.filter(org=org, is_current=True)
        .select_related("employee", "post", "org")
        .order_by("employee__last_name", "employee__first_name")
    )
    context = {
        "org": org,
        "current": current,
        "versions": versions,
        "employees": employees,
    }
    return render(request, "rca/org_detail.html", context)


def post_list(request):
    query = request.GET.get("q", "").strip()
    show_history = request.GET.get("history") == "1"

    versions = PostVersion.objects.select_related("post").order_by("post__code", "-valid_from")
    if not show_history:
        versions = versions.filter(is_current=True)
    if query:
        versions = versions.filter(
            Q(post__code__icontains=query) | Q(name__icontains=query)
        )

    context = {
        "query": query,
        "show_history": show_history,
        "post_versions": versions,
    }
    return render(request, "rca/post_list.html", context)


def post_detail(request, code: str):
    post = get_object_or_404(Post, code=code)
    versions = post.versions.order_by("-valid_from")
    current = versions.filter(is_current=True).first()
    employees = (
        EmployeeSnapshot.objects.filter(post=post, is_current=True)
        .select_related("employee", "post", "org")
        .order_by("employee__last_name", "employee__first_name")
    )
    context = {
        "post": post,
        "current": current,
        "versions": versions,
        "employees": employees,
    }
    return render(request, "rca/post_detail.html", context)


def employee_list(request):
    query = request.GET.get("q", "").strip()
    org_code = request.GET.get("org", "").strip()
    post_code = request.GET.get("post", "").strip()
    status = request.GET.get("status", "active")
    show_history = request.GET.get("history") == "1"

    snapshots = EmployeeSnapshot.objects.select_related("employee", "org", "post").order_by(
        "employee__last_name",
        "employee__first_name",
        "-valid_from",
    )

    if not show_history:
        snapshots = snapshots.filter(is_current=True)

    if status == "fired":
        snapshots = snapshots.filter(employee__is_fired_current=True)
    elif status == "active":
        snapshots = snapshots.filter(employee__is_fired_current=False)

    if org_code:
        snapshots = snapshots.filter(org__code=org_code)
    if post_code:
        snapshots = snapshots.filter(post__code=post_code)

    if query:
        snapshots = snapshots.filter(
            Q(employee__last_name__icontains=query)
            | Q(employee__first_name__icontains=query)
            | Q(employee__middle_name__icontains=query)
            | Q(employee__snils_norm__icontains=query)
            | Q(employee__tab_norm_current__icontains=query)
            | Q(org__code__icontains=query)
            | Q(post__code__icontains=query)
        )

    org_choices = OrgVersion.objects.filter(is_current=True).order_by("name")
    post_choices = PostVersion.objects.filter(is_current=True).order_by("name")

    context = {
        "query": query,
        "org_code": org_code,
        "post_code": post_code,
        "status": status,
        "show_history": show_history,
        "snapshots": snapshots,
        "org_choices": org_choices,
        "post_choices": post_choices,
    }
    return render(request, "rca/employee_list.html", context)


def employee_detail(request, snils: str):
    employee = get_object_or_404(Employee, snils_norm=snils)
    snapshots = employee.snapshots.select_related("org", "post").order_by("-valid_from")
    current = snapshots.filter(is_current=True).first()
    context = {
        "employee": employee,
        "current": current,
        "snapshots": snapshots,
    }
    return render(request, "rca/employee_detail.html", context)
