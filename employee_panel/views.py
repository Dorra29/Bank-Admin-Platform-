# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from core.decorators import role_required
from ad_management.services import get_ad_user_profile


@login_required
@role_required("GG_Employees")
def employee_dashboard(request):
    profile = get_ad_user_profile(request.user.username)
    return render(
        request,
        "employee_dashboard.html",
        {"profile": profile},
    )
