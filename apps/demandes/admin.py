from django.contrib import admin
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from .models import DemandesDemande, DemandesPieceJointe

@admin.register(DemandesDemande)
class DemandeAdmin(admin.ModelAdmin):
    list_display = ('reference', 'statut', 'created_at')
    list_filter = ('statut', 'created_at')
    search_fields = ('reference', 'email_reception')
    readonly_fields = ('created_at', 'updated_at')

    actions = ['envoyer_document_email']

    def envoyer_document_email(self, request, queryset):
        for demande in queryset:
            if not demande.email_reception:
                self.message_user(request, f"Demande {demande.reference} : pas d'email défini", level='error')
                continue

            # Vérifier qu'il y a un document généré
            if not demande.document_genere:
                self.message_user(request, f"Demande {demande.reference} : aucun document généré", level='error')
                continue

            try:
                # Ouvrir le fichier généré
                with open(demande.document_genere.path, 'rb') as f:
                    contenu = f.read()
                
                email = EmailMessage(
                    subject=f"Votre document - Demande {demande.reference}",
                    body=f"Bonjour,\n\nVotre demande {demande.reference} a été traitée.\n\nCordialement,\nL'Ordre des Notaires",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[demande.email_reception]
                )
                email.attach(demande.document_genere.name, contenu, 'application/pdf')
                email.send()

                # Mettre à jour la demande
                demande.statut = 'document_envoye_email'
                demande.date_envoi_email = timezone.now()
                demande.save()

                self.message_user(request, f"Document envoyé pour la demande {demande.reference}")

            except Exception as e:
                self.message_user(request, f"Erreur pour la demande {demande.reference} : {str(e)}", level='error')

    envoyer_document_email.short_description = "Envoyer le document par email"


@admin.register(DemandesPieceJointe)
class PieceJointeAdmin(admin.ModelAdmin):
    list_display = ('demande', 'type_piece', 'nom_original', 'taille_formatee', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'nom_original', 'taille_fichier')
    fieldsets = (
        ('Informations', {'fields': ('demande', 'type_piece', 'fichier', 'description')}),
        ('Détails', {'fields': ('nom_original', 'taille_fichier', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
