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
    add_user_to_group,
    remove_user_from_group,
    list_all_ad_users,
    get_user_detail,
    delete_ad_user,
    move_ad_user,
)

# Maps the role picked in the form to where the account lands and which
# AD group grants it access — Managers live in OU=Employees, not their own OU.
ROLE_TO_OU_AND_GROUP = {
    "Admin": ("Admins", "GG_Admins"),
    "Manager": ("Employees", "GG_Managers"),
    "Employee": ("Employees", "GG_Employees"),
}


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
        role = request.POST["role"]

        ou, group_name = ROLE_TO_OU_AND_GROUP.get(role, (None, None))
        if not ou:
            return render(
                request,
                "admin_panel/create_user.html",
                {"message": "Invalid role selected.", "success": False},
            )

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

        if result["success"]:
            group_result = add_user_to_group(username, group_name)
            if not group_result["success"]:
                # Account exists but has no group yet — surface this clearly
                # rather than silently reporting a plain "success".
                result = {
                    "success": False,
                    "message": f"User created, but couldn't assign group {group_name}: {group_result['message']}",
                }
            else:
                result = {"success": True, "message": f"User created and assigned to {group_name}."}

        return render(
            request,
            "admin_panel/create_user.html",
            {"message": result["message"], "success": result["success"]},
        )

    return render(
        request,
        "admin_panel/create_user.html"
    )


@login_required
@role_required("GG_Admins")
def list_users(request):
    query = request.GET.get("q", "").strip()
    users = list_all_ad_users(query=query or None)
    return render(
        request,
        "admin_panel/users.html",
        {"users": users, "query": query},
    )


AD_ACTIONS = {
    "enable": lambda username, post: enable_ad_user(username),
    "disable": lambda username, post: disable_ad_user(username),
    "unlock": lambda username, post: unlock_ad_user(username),
    "reset_password": lambda username, post: reset_ad_password(username, post.get("new_password", "")),
    "add_group": lambda username, post: add_user_to_group(username, post.get("group_name", "")),
    "remove_group": lambda username, post: remove_user_from_group(username, post.get("group_name", "")),
    "move_ou": lambda username, post: move_ad_user(username, post.get("target_ou", "")),
    "delete": lambda username, post: delete_ad_user(username),
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

        # Deleted users obviously can't be looked up afterward.
        user_detail = get_user_detail(username) if action != "delete" else None

        return render(
            request,
            "admin_panel/manage_user.html",
            {
                "message": result["message"],
                "success": result["success"],
                "prefill_username": username,
                "user_detail": user_detail,
            },
        )

    username = request.GET.get("username", "")
    user_detail = get_user_detail(username) if username else None

    return render(
        request,
        "admin_panel/manage_user.html",
        {"prefill_username": username, "user_detail": user_detail},
    )
