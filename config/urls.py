from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dunbud.urls")),
    path("users/", include("users.urls")),
    path("blog/", include("blog.urls", namespace="blog")),
]

# Custom Error Handlers
handler400 = "dunbud.views.errors.bad_request"
handler403 = "dunbud.views.errors.permission_denied"
handler404 = "dunbud.views.errors.page_not_found"
handler500 = "dunbud.views.errors.server_error"
