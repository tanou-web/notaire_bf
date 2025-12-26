from django.contrib import admin
from .models import CommunicationsEmaillog


@admin.register(CommunicationsEmaillog)
class CommunicationsEmailLogAdmin(admin.ModelAdmin):
    list_display = ('destinataire', 'sujet', 'statut', 'created_at')
    search_fields = ('destinataire', 'sujet', 'contenu')
    readonly_fields = ('type_email', 'destinataire', 'sujet', 'contenu', 'statut', 'message_id', 'erreur', 'created_at', 'updated_at')
