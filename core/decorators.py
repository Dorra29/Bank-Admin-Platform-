import logging
from functools import wraps

from django.shortcuts import redirect

logger = logging.getLogger(__name__)


def role_required(*required_roles):
    """
    Accepts one or more roles, e.g. role_required("GG_Admins") or
    role_required("GG_Admins", "GG_SupportAdmins") for views shared
    across roles — access is granted if the session's ad_groups match
    ANY of the required roles.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            groups = request.session.get("ad_groups", [])
            logger.debug("Checking roles %s against session groups %s", required_roles, groups)

            role_found = any(
                required_role in group
                for group in groups
                for required_role in required_roles
            )

            if role_found:
                return view_func(request, *args, **kwargs)

            logger.info("Access denied for roles %s (session groups: %s)", required_roles, groups)
            return redirect("/no-access/")

        return wrapper

    return decorator
