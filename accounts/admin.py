from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from .forms import CtsUserChangeForm, CtsUserCreationForm
from .models import CtsUser


class CtsUserAdmin(UserAdmin):
    form = CtsUserChangeForm
    add_form = CtsUserCreationForm
    list_display = ('email', 'name', 'role', 'is_staff')
    ordering = ('name', 'email',)
    search_fields = ('name', 'email')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('name',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (None, {'fields': ('role', 'mobile', 'code', 'skype', 'notes', 'deviceid')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}),
    )


admin.site.register(CtsUser, CtsUserAdmin)
