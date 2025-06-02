from django.urls import path

from user.views import CreateUserView, RetrieveUpdateUserView

urlpatterns = [
    path("register/", CreateUserView.as_view(), name="register_user"),
    path("me/", RetrieveUpdateUserView.as_view(), name="me"),
]

app_name = "user"
