from functools import wraps

from django.shortcuts import redirect
from django.http import HttpResponseForbidden



def role_required(required_role):

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


                if required_role in group:

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