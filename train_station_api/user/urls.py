from django.urls import path
from rest_framework.authtoken import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from user.views import CreateUserView, RetrieveUpdateUserView, CreateTokenView

urlpatterns = [
    path("register/", CreateUserView.as_view(), name="register_user"),
    path("login/", CreateTokenView.as_view(), name="get-token"),
    path(
        "api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"
    ),
    path(
        "api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"
    ),
    path("me/", RetrieveUpdateUserView.as_view(), name="me"),
]

app_name = "user"
