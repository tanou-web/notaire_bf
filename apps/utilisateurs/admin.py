from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, VerificationVerificationtoken

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Interface d'administration personnalisée pour les utilisateurs"""
    
    list_display = ('username', 'email', 'nom', 'prenom', 'telephone', 
                    'is_staff', 'is_superuser', 'is_active', 'email_verifie')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'email_verifie', 'telephone_verifie')
    search_fields = ('username', 'email', 'nom', 'prenom', 'telephone')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Informations personnelles'), {
            'fields': ('nom', 'prenom', 'email', 'telephone')
        }),
        (_('Vérifications'), {
            'fields': ('email_verifie', 'telephone_verifie')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Dates importantes'), {
            'fields': ('last_login', 'date_joined', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2',
                       'nom', 'prenom', 'telephone',
                       'is_staff', 'is_superuser', 'is_active'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login', 'updated_at')
    
    def get_readonly_fields(self, request, obj=None):
        """Empêcher les non-superutilisateurs de modifier certains champs"""
        if not request.user.is_superuser:
            return self.readonly_fields + ('is_superuser', 'user_permissions')
        return self.readonly_fields
    
    def get_queryset(self, request):
        """Filtrer les utilisateurs selon les permissions"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(is_superuser=False)

@admin.register(VerificationVerificationtoken)
class VerificationTokenAdmin(admin.ModelAdmin):
    """Interface d'administration pour les tokens de vérification"""
    
    list_display = ('id', 'user', 'type_token', 'used', 'expires_at', 'created_at')
    list_filter = ('type_token', 'used', 'created_at')
    search_fields = ('user__username', 'user__email', 'token')
    readonly_fields = ('token', 'expires_at', 'created_at', 'updated_at')
    ordering = ('-created_at',)

# Personnaliser le titre de l'admin
admin.site.site_header = "Administration Ordre des Notaires BF"
admin.site.site_title = "Portail d'administration"
admin.site.index_title = "Tableau de bord"