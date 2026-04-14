from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("checker.urls")),
    path("admin/", admin.site.urls),
]
