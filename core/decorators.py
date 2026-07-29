from functools import wraps

from django.shortcuts import redirect
from django.http import HttpResponseForbidden



def role_required(*required_roles):
    # Accepts one or more roles, e.g. role_required("GG_Admins") or
    # role_required("GG_Admins", "GG_SupportAdmins") for views shared
    # across roles — access is granted if the session's ad_groups match
    # ANY of the required roles.

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):


            groups = request.session.get(
                "ad_groups",
                []
            )


            print("CHECKING ROLE:")
            print(groups)



            role_found = False



            for group in groups:


                if any(required_role in group for required_role in required_roles):

                    role_found = True
                    break



            if role_found:

                return view_func(
                    request,
                    *args,
                    **kwargs
                )


            else:

                return redirect(
                    "/no-access/"
                )


        return wrapper


    return decorator
