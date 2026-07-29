# Create your views here.
from datetime import date

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
    set_password_expiration,
    clear_password_expiration,
    get_password_expiration,
)

# Maps the role picked in the form to where the account lands and which
# AD group grants it access — Managers live in OU=Employees, not their own OU.
# Support Admin lives alongside Admin in OU=Admins: it's an admin-tier
# account, just without delete rights.
ROLE_TO_OU_AND_GROUP = {
    "Admin": ("Admins", "GG_Admins"),
    "Support Admin": ("Admins", "GG_SupportAdmins"),
    "Manager": ("Employees", "GG_Managers"),
    "Employee": ("Employees", "GG_Employees"),
}

# Views in this module are shared by both admin-tier roles. Support Admins
# get everything Admins get here EXCEPT deleting accounts (enforced in
# manage_user below) — they do get the password-expiration actions.
ADMIN_TIER_ROLES = ("GG_Admins", "GG_SupportAdmins")


@login_required
@role_required(*ADMIN_TIER_ROLES)
def admin_dashboard(request):

    stats = get_admin_dashboard_stats()

    return render(
        request,
        "admin_dashboard.html",
        {"stats": stats}
    )


@login_required
@role_required(*ADMIN_TIER_ROLES)
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
@role_required(*ADMIN_TIER_ROLES)
def list_users(request):
    query = request.GET.get("q", "").strip()
    users = list_all_ad_users(query=query or None)
    return render(
        request,
        "admin_panel/users.html",
        {"users": users, "query": query},
    )


def _set_password_expiration_action(username, post, requesting_user):
    raw_date = post.get("expires_on", "")
    try:
        expires_on = date.fromisoformat(raw_date)
    except ValueError:
        return {"success": False, "message": "Enter a valid expiration date."}
    return set_password_expiration(username, expires_on, set_by=requesting_user)


# Handlers all take (username, post, requesting_user) so the ones that need
# an audit trail (set_password_expiration) or the raw POST data can get it,
# even though most actions only need the username.
AD_ACTIONS = {
    "enable": lambda username, post, user: enable_ad_user(username),
    "disable": lambda username, post, user: disable_ad_user(username),
    "unlock": lambda username, post, user: unlock_ad_user(username),
    "reset_password": lambda username, post, user: reset_ad_password(username, post.get("new_password", "")),
    "add_group": lambda username, post, user: add_user_to_group(username, post.get("group_name", "")),
    "remove_group": lambda username, post, user: remove_user_from_group(username, post.get("group_name", "")),
    "move_ou": lambda username, post, user: move_ad_user(username, post.get("target_ou", "")),
    "delete": lambda username, post, user: delete_ad_user(username),
    "set_password_expiration": _set_password_expiration_action,
    "clear_password_expiration": lambda username, post, user: clear_password_expiration(username),
}

# Support Admins get every action here except these — currently just
# account deletion, per the role's definition.
ADMIN_ONLY_ACTIONS = {"delete"}


@login_required
@role_required(*ADMIN_TIER_ROLES)
def manage_user(request):

    is_full_admin = any(
        "GG_Admins" in group for group in request.session.get("ad_groups", [])
    )

    if request.method == "POST":

        username = request.POST.get("username")
        action = request.POST.get("action")

        handler = AD_ACTIONS.get(action)
        if not handler:
            return render(
                request,
                "admin_panel/manage_user.html",
                {"message": "Unknown action.", "success": False, "can_delete": is_full_admin},
            )

        if action in ADMIN_ONLY_ACTIONS and not is_full_admin:
            return render(
                request,
                "admin_panel/manage_user.html",
                {
                    "message": "Support Admins can't delete accounts — ask an Admin.",
                    "success": False,
                    "prefill_username": username,
                    "user_detail": get_user_detail(username) if username else None,
                    "password_expiration": get_password_expiration(username) if username else None,
                    "can_delete": is_full_admin,
                },
            )

        result = handler(username, request.POST, request.user)

        # Deleted users obviously can't be looked up afterward.
        user_detail = get_user_detail(username) if action != "delete" else None
        password_expiration = get_password_expiration(username) if action != "delete" else None

        return render(
            request,
            "admin_panel/manage_user.html",
            {
                "message": result["message"],
                "success": result["success"],
                "prefill_username": username,
                "user_detail": user_detail,
                "password_expiration": password_expiration,
                "can_delete": is_full_admin,
            },
        )

    username = request.GET.get("username", "")
    user_detail = get_user_detail(username) if username else None
    password_expiration = get_password_expiration(username) if username else None

    return render(
        request,
        "admin_panel/manage_user.html",
        {
            "prefill_username": username,
            "user_detail": user_detail,
            "password_expiration": password_expiration,
            "can_delete": is_full_admin,
        },
    )
