# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.decorators import role_required
from ad_management.services import create_ad_user


@login_required
@role_required("GG_Admins")
def admin_dashboard(request):

    return render(
        request,
        "admin_dashboard.html"
    )

@login_required
def create_user(request):

    if request.method == "POST":


        username = request.POST["username"]

        first_name = request.POST["first_name"]

        last_name = request.POST["last_name"]

        password = request.POST["password"]

        ou = request.POST["ou"]


        result = create_ad_user(
            username,
            first_name,
            last_name,
            password,
            ou 
        )


        if result:

            message = "User created successfully"

        else:

            message = "User creation failed"



        return render(
            request,
            "admin_panel/create_user.html",
            {
                "message":message
            }
        )



    return render(
        request,
        "admin_panel/create_user.html"
    )