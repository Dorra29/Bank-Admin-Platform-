import logging

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from ad_management.services import get_password_expiration

logger = logging.getLogger(__name__)


def welcome_view(request):
    if request.user.is_authenticated:
        return redirect("/dashboard/")

    return render(request, "welcome.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        logger.debug("Login attempt for '%s'", username)

        try:
            user = authenticate(request, username=username, password=password)

            if user is not None:
                expiration = get_password_expiration(username)

                if expiration and expiration.is_expired():
                    logger.info("Login blocked, expired password for '%s'", username)
                    return render(
                        request,
                        "login.html",
                        {
                            "error": "Your password expired on "
                            f"{expiration.expires_on}. Contact an admin to reset it."
                        },
                    )

                login(request, user)

                groups = getattr(user, "ad_groups", [])
                logger.info("Login success for '%s', AD groups: %s", username, groups)

                request.session["ad_groups"] = groups
                request.session["username"] = username

                return redirect("/dashboard/")

            logger.info("Login failed: invalid credentials for '%s'", username)
            return render(request, "login.html", {"error": "Invalid username or password"})

        except Exception:
            logger.exception("LDAP error during login for '%s'", username)
            return render(request, "login.html", {"error": "LDAP connection error"})

    # GET request
    return render(request, "login.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("/login/")
