from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = [
        "email",
        "username",
        "location",
        "is_staff",
        "is_test_user",
    ]

    fieldsets = list(UserAdmin.fieldsets or []) + [
        (None, {"fields": ("bio", "location", "website", "is_test_user")}),
    ]
    add_fieldsets = list(UserAdmin.add_fieldsets or []) + [
        (None, {"fields": ("bio", "location", "website", "is_test_user")}),
    ]
