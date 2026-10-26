from django.contrib import admin
from .models import RoleUser

@admin.register(RoleUser)
class RoleUserAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "role")
    search_fields = ("name", "email")
    list_filter = ("role",)