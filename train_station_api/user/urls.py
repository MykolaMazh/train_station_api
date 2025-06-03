from django.urls import path
from rest_framework.authtoken import views

from user.views import CreateUserView, RetrieveUpdateUserView, CreateTokenView

urlpatterns = [
    path("register/", CreateUserView.as_view(), name="register_user"),
    path("login/", CreateTokenView.as_view(), name="get-token"),
    path("me/", RetrieveUpdateUserView.as_view(), name="me"),
]

app_name = "user"
