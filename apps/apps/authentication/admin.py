from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, CodeOTP


@admin.register(User)
class UtilisateurAdmin(UserAdmin):
    list_display  = ('username', 'get_full_name', 'email', 'role', 'is_active')
    list_filter   = ('role', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    fieldsets     = UserAdmin.fieldsets + (
        ('Informations ESCEP', {'fields': ('role', 'telephone')}),
    )


@admin.register(CodeOTP)
class CodeOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'cree_le', 'utilise', 'tentatives')
    list_filter  = ('utilise',)
