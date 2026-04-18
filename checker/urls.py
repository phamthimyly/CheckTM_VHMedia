from django.urls import path

from .views import dang_nhap, dang_xuat, dashboard, home, quan_ly_tai_khoan

urlpatterns = [
    path("", home, name="home"),
    path("login/", dang_nhap, name="login"),
    path("logout/", dang_xuat, name="logout"),
    path("dashboard/", dashboard, name="dashboard"),
    path("accounts/", quan_ly_tai_khoan, name="accounts"),
]
