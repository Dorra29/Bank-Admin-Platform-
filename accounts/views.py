from urllib import request

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required



def welcome_view(request):

    if request.user.is_authenticated:
        return redirect("/dashboard/")

    return render(
        request,
        "welcome.html"
    )


def login_view(request):

    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]

        print("Connecting to LDAP...")

        try:

            # Django LDAP authentication
            user = authenticate(
                request,
                username=username,
                password=password
            )


            if user is not None:

                login(request, user)

                print("LOGIN SUCCESS")


                # ==============================
                # READ AD GROUPS
                # ==============================

                groups = getattr(user, "ad_groups", [])

                print("AD GROUPS:")
                print(groups)

                request.session["ad_groups"] = groups
                request.session["username"] = username


                # Save groups in session

                request.session["ad_groups"] = groups
                request.session["username"] = username


                return redirect("/dashboard/")


            else:

                print("INVALID CREDENTIALS")

                return render(
                    request,
                    "login.html",
                    {
                        "error": "Invalid username or password"
                    }
                )


        except Exception as e:

            print(
                "LDAP ERROR:",
                e
            )

            return render(
                request,
                "login.html",
                {
                    "error": "LDAP connection error"
                }
            )


    # GET request

    return render(
        request,
        "login.html"
    )



@login_required
def logout_view(request):

    logout(request)

    return redirect("/login/")