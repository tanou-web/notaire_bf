from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, VerificationVerificationtoken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Administration personnalisée des utilisateurs"""

    list_display = (
        'username', 'email', 'nom', 'prenom', 'telephone',
        'is_staff', 'is_superuser', 'is_active', 'email_verifie'
    )
    list_filter = (
        'is_staff', 'is_superuser', 'is_active',
        'email_verifie', 'telephone_verifie'
    )
    search_fields = ('username', 'email', 'nom', 'prenom', 'telephone')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),

        (_('Informations personnelles'), {
            'fields': ('nom', 'prenom', 'email', 'telephone'),
        }),

        (_('Vérifications'), {
            'fields': ('email_verifie', 'telephone_verifie'),
        }),

        (_('Statut'), {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),

        (_('Dates importantes'), {
            'fields': ('last_login', 'date_joined', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email',
                'password1', 'password2',
                'nom', 'prenom', 'telephone',
                'is_active', 'is_staff', 'is_superuser'
            ),
        }),
    )

    readonly_fields = ('date_joined', 'last_login', 'updated_at')

    filter_horizontal = ()


    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(is_superuser=False)


@admin.register(VerificationVerificationtoken)
class VerificationTokenAdmin(admin.ModelAdmin):
    """Administration des tokens de vérification"""

    list_display = ('id', 'user', 'type_token', 'expires_at')
    list_filter = ('type_token',)
    search_fields = ('user__username', 'user__email', 'token')
    readonly_fields = ('token', 'expires_at')
    ordering = ('-id',)


# Titres Admin
admin.site.site_header = "Administration Ordre des Notaires BF"
admin.site.site_title = "Portail d'administration"
admin.site.index_title = "Tableau de bord"
