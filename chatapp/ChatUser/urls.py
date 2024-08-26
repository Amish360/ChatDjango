from django.urls import path

from .views import (
    CustomUserDetail,
    CustomUserList,
    user_login,
    OTPRequestView,
    OTPVerifyView,
    PasswordResetView
)

urlpatterns = [
    path("register/", CustomUserList.as_view(), name="user-list"),
    path("register/<int:pk>/", CustomUserDetail.as_view(), name="user-detail"),
    path("login/", user_login, name="user_login"),
    path('otp/request/', OTPRequestView.as_view(), name='otp-request'),
    path('otp/verify/', OTPVerifyView.as_view(), name='otp-verify'),
    path('password/reset/', PasswordResetView.as_view(), name='password-reset'),
]