from django.urls import path
from . import views


urlpatterns = [

    path(
        "",
        views.admin_dashboard,
        name="admin_dashboard"
    ),

    path(
        "create-user/",
        views.create_user,
        name="create_user"
    ),


]