from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dunbud.urls")),
    path("users/", include("users.urls")),
    path("blog/", include("blog.urls", namespace="blog")),
]
