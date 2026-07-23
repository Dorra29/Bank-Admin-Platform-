# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from core.decorators import role_required


@login_required
@role_required("GG_Employees")
def employee_dashboard(request):
    return render(
        request,
        "employee_dashboard.html"
    )