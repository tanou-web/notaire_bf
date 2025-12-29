# apps/demandes/admin.py - VERSION ULTRA SIMPLE ET FONCTIONNELLE
from django.contrib import admin
from rest_framework.permissions import IsAdminUser
from .views import viewsets

class AdminOnlyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]

# Import sécurisé
try:
    from .models import DemandesDemande
except ImportError:
    # Si le modèle n'existe pas, ne rien faire
    DemandesDemande = None

if DemandesDemande:
    @admin.register(DemandesDemande)
    class DemandeAdmin(admin.ModelAdmin):
        """Admin ultra simple pour les demandes"""
        list_display = ('reference', 'statut', 'created_at')
        list_filter = ('statut', 'created_at')
        search_fields = ('reference',  'client_email')
        readonly_fields = ('created_at', 'updated_at')