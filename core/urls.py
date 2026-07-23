from django.urls import path
from . import views


urlpatterns = [

    path(
        "",
        views.no_access,
        name="no_access"
    ),

]