# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.decorators import role_required
from ad_management.services import (
    create_ad_user,
    enable_ad_user,
    disable_ad_user,
    reset_ad_password,
    unlock_ad_user,
    get_admin_dashboard_stats,
)


@login_required
@role_required("GG_Admins")
def admin_dashboard(request):

    stats = get_admin_dashboard_stats()

    return render(
        request,
        "admin_dashboard.html",
        {"stats": stats}
    )


@login_required
@role_required("GG_Admins")
def create_user(request):

    if request.method == "POST":

        username = request.POST["username"]
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        password = request.POST["password"]
        ou = request.POST["ou"]

        # NOTE: called with keyword arguments on purpose — the previous
        # positional call scrambled first_name/last_name/username because
        # the call order didn't match the function signature.
        result = create_ad_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=password,
            ou=ou,
        )

        return render(
            request,
            "admin_panel/create_user.html",
            {
                "message": result["message"] if not result["success"] else "User created successfully",
                "success": result["success"],
            }
        )

    return render(
        request,
        "admin_panel/create_user.html"
    )


AD_ACTIONS = {
    "enable": lambda username, post: enable_ad_user(username),
    "disable": lambda username, post: disable_ad_user(username),
    "unlock": lambda username, post: unlock_ad_user(username),
    "reset_password": lambda username, post: reset_ad_password(username, post.get("new_password", "")),
}


@login_required
@role_required("GG_Admins")
def manage_user(request):

    if request.method == "POST":

        username = request.POST.get("username")
        action = request.POST.get("action")

        handler = AD_ACTIONS.get(action)
        if not handler:
            return render(
                request,
                "admin_panel/manage_user.html",
                {"message": "Unknown action.", "success": False},
            )

        result = handler(username, request.POST)
        return render(
            request,
            "admin_panel/manage_user.html",
            {"message": result["message"], "success": result["success"]},
        )

    return render(
        request,
        "admin_panel/manage_user.html"
    )
