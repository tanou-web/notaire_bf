# apps/demandes/admin.py
from django.contrib import admin
from django.contrib.admin import ModelAdmin, TabularInline
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum
from rangefilter.filters import DateRangeFilter
from import_export.admin import ExportActionMixin
from import_export import resources
from .models import DemandesDemande

class DemandeResource(resources.ModelResource):
    """Resource pour l'export/import des demandes"""
    class Meta:
        model = DemandesDemande
        fields = (
            'id', 'reference', 'utilisateur__email', 
            'document__nom', 'statut', 'montant_total',
            'frais_commission', 'notaire__nom_complet',
            'created_at', 'updated_at'
        )
        export_order = fields

class DocumentGenereFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les documents générés"""
    title = 'Document généré'
    parameter_name = 'document_genere'
    
    def lookups(self, request, model_admin):
        return (
            ('oui', 'Avec document'),
            ('non', 'Sans document'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'oui':
            return queryset.exclude(document_genere='')
        if self.value() == 'non':
            return queryset.filter(document_genere='')
        return queryset

@admin.register(DemandesDemande)
class DemandeAdmin(ExportActionMixin, ModelAdmin):
    """Configuration de l'admin pour les demandes"""
    
    resource_class = DemandeResource
    
    # Configuration de l'affichage liste
    list_display = [
        'reference_link', 'utilisateur_email', 'document_nom',
        'statut_badge', 'montant_total_fmt', 'notaire_nom',
        'created_at_fmt', 'actions'
    ]
    
    list_filter = [
        'statut',
        DocumentGenereFilter,
        ('created_at', DateRangeFilter),
        ('date_attribution', DateRangeFilter),
        'notaire',
        'document',
    ]
    
    search_fields = [
        'reference',
        'utilisateur__email',
        'utilisateur__first_name',
        'utilisateur__last_name',
        'email_reception',
        'donnees_formulaire',
    ]
    
    readonly_fields = [
        'reference', 'created_at', 'updated_at',
        'montant_total', 'frais_commission',
        'date_attribution', 'date_envoi_email',
        'statut_timeline'
    ]
    
    fieldsets = (
        ('Informations Générales', {
            'fields': (
                'reference', 'utilisateur', 'document',
                'statut', 'statut_timeline'
            )
        }),
        ('Données de la Demande', {
            'fields': (
                'email_reception', 'donnees_formulaire_preview',
                'montant_total', 'frais_commission'
            )
        }),
        ('Traitement', {
            'fields': (
                'notaire', 'date_attribution',
                'document_genere', 'date_envoi_email'
            )
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    raw_id_fields = ['utilisateur', 'document', 'notaire']
    
    actions = [
        'marquer_comme_en_traitement',
        'assigner_notaire_en_masse',
        'generer_documents',
        'envoyer_emails_rappel',
        'export_selection_excel',
    ]
    
    # Champs personnalisés pour l'affichage
    def reference_link(self, obj):
        url = reverse('admin:demandes_demande_change', args=[obj.id])
        return format_html('<a href="{}">{}</a>', url, obj.reference)
    reference_link.short_description = 'Référence'
    reference_link.admin_order_field = 'reference'
    
    def utilisateur_email(self, obj):
        return obj.utilisateur.email if obj.utilisateur else '-'
    utilisateur_email.short_description = 'Utilisateur'
    utilisateur_email.admin_order_field = 'utilisateur__email'
    
    def document_nom(self, obj):
        return obj.document.nom if obj.document else '-'
    document_nom.short_description = 'Document'
    document_nom.admin_order_field = 'document__nom'
    
    def statut_badge(self, obj):
        colors = {
            'brouillon': 'gray',
            'attente_formulaire': 'orange',
            'attente_paiement': 'yellow',
            'en_attente_traitement': 'blue',
            'en_traitement': 'purple',
            'document_envoye_email': 'green',
            'annule': 'red',
        }
        color = colors.get(obj.statut, 'gray')
        return format_html(
            '<span style="display:inline-block; padding:2px 8px; '
            'background-color:{}; color:white; border-radius:10px; '
            'font-size:12px;">{}</span>',
            color, obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'
    statut_badge.admin_order_field = 'statut'
    
    def montant_total_fmt(self, obj):
        return f"{obj.montant_total:,.0f} FCFA"
    montant_total_fmt.short_description = 'Montant'
    montant_total_fmt.admin_order_field = 'montant_total'
    
    def notaire_nom(self, obj):
        if obj.notaire:
            return f"{obj.notaire.nom} {obj.notaire.prenom}"
        return '-'
    notaire_nom.short_description = 'Notaire'
    notaire_nom.admin_order_field = 'notaire__nom'
    
    def created_at_fmt(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M')
    created_at_fmt.short_description = 'Créée le'
    created_at_fmt.admin_order_field = 'created_at'
    
    def actions(self, obj):
        buttons = []
        
        # Bouton assigner
        if obj.statut in ['en_attente_traitement', 'attente_paiement']:
            assign_url = reverse('admin:demande-assigner-notaire', args=[obj.id])
            buttons.append(f'''
                <a href="{assign_url}" class="button" style="background-color:#4CAF50;color:white;padding:5px 10px;border-radius:3px;text-decoration:none;">
                    Assigner
                </a>
            ''')
        
        # Bouton traiter
        if obj.statut == 'en_traitement':
            traiter_url = reverse('admin:demande-completer-traitement', args=[obj.id])
            buttons.append(f'''
                <a href="{traiter_url}" class="button" style="background-color:#2196F3;color:white;padding:5px 10px;border-radius:3px;text-decoration:none;">
                    Traiter
                </a>
            ''')
        
        # Bouton email
        if obj.email_reception:
            buttons.append(f'''
                <a href="mailto:{obj.email_reception}" class="button" style="background-color:#FF9800;color:white;padding:5px 10px;border-radius:3px;text-decoration:none;">
                    Email
                </a>
            ''')
        
        return format_html(' '.join(buttons))
    actions.short_description = 'Actions'
    
    # Champs personnalisés pour le formulaire d'édition
    def donnees_formulaire_preview(self, obj):
        """Affiche les données du formulaire de manière lisible"""
        if not obj.donnees_formulaire:
            return '-'
        
        html = '<div style="max-height:200px;overflow-y:auto;background:#f9f9f9;padding:10px;border:1px solid #ddd;">'
        for key, value in obj.donnees_formulaire.items():
            html += f'<p><strong>{key}:</strong> {value}</p>'
        html += '</div>'
        return format_html(html)
    donnees_formulaire_preview.short_description = 'Données du formulaire'
    
    def statut_timeline(self, obj):
        """Affiche une timeline des statuts"""
        timeline_data = {
            'Créée': obj.created_at,
            'Formulaire rempli': obj.updated_at if obj.donnees_formulaire else None,
            'Paiement validé': obj.updated_at if obj.statut in ['en_attente_traitement', 'en_traitement'] else None,
            'Notaire assigné': obj.date_attribution,
            'Document envoyé': obj.date_envoi_email,
        }
        
        html = '<div style="border-left:3px solid #4CAF50;padding-left:15px;margin-left:5px;">'
        for step, date in timeline_data.items():
            if date:
                html += f'''
                <div style="margin-bottom:10px;position:relative;">
                    <div style="position:absolute;left:-20px;top:0;width:10px;height:10px;background-color:#4CAF50;border-radius:50%;"></div>
                    <strong>{step}</strong><br>
                    <small>{date.strftime('%d/%m/%Y %H:%M')}</small>
                </div>
                '''
        html += '</div>'
        return format_html(html)
    statut_timeline.short_description = 'Historique'
    
    # Actions personnalisées
    def marquer_comme_en_traitement(self, request, queryset):
        """Marquer les demandes sélectionnées comme en traitement"""
        updated = queryset.filter(
            statut='en_attente_traitement'
        ).update(statut='en_traitement')
        
        self.message_user(
            request, 
            f"{updated} demande(s) marquée(s) comme en traitement"
        )
    marquer_comme_en_traitement.short_description = "Marquer comme en traitement"
    
    def assigner_notaire_en_masse(self, request, queryset):
        """Assigner un notaire à plusieurs demandes"""
        from django.shortcuts import render
        from apps.notaires.models import NotairesNotaire
        
        if 'apply' in request.POST:
            notaire_id = request.POST.get('notaire')
            if notaire_id:
                notaire = NotairesNotaire.objects.get(id=notaire_id)
                queryset.update(notaire=notaire, date_attribution=timezone.now())
                self.message_user(request, f"Notaire assigné à {queryset.count()} demande(s)")
                return
        
        notaires = NotairesNotaire.objects.filter(actif=True)
        context = {
            'demandes': queryset,
            'notaires': notaires,
            'action_name': 'assigner_notaire_en_masse',
        }
        return render(request, 'admin/assigner_notaire_masse.html', context)
    assigner_notaire_en_masse.short_description = "Assigner un notaire (masse)"
    
    def generer_documents(self, request, queryset):
        """Générer les documents PDF pour les demandes sélectionnées"""
        from django.http import HttpResponse
        import zipfile
        import io
        
        # Simuler la génération de fichiers
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for demande in queryset:
                # Ici, vous intégrerez votre logique de génération PDF
                content = f"Document pour {demande.reference}".encode()
                zip_file.writestr(f"{demande.reference}.pdf", content)
        
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="documents_generes.zip"'
        return response
    generer_documents.short_description = "Générer les documents PDF"
    
    def envoyer_emails_rappel(self, request, queryset):
        """Envoyer des emails de rappel"""
        import threading
        from django.core.mail import send_mail
        
        def envoyer_email_async(demande):
            send_mail(
                f"Rappel - Demande {demande.reference}",
                f"Votre demande {demande.reference} est en statut {demande.get_statut_display()}",
                'noreply@notaires-burkina.bf',
                [demande.email_reception],
                fail_silently=True,
            )
        
        for demande in queryset:
            if demande.email_reception:
                threading.Thread(target=envoyer_email_async, args=(demande,)).start()
        
        self.message_user(
            request,
            f"Emails de rappel envoyés pour {queryset.count()} demande(s)"
        )
    envoyer_emails_rappel.short_description = "Envoyer emails de rappel"
    
    def export_selection_excel(self, request, queryset):
        """Exporter la sélection en Excel"""
        import pandas as pd
        from django.http import HttpResponse
        
        data = []
        for demande in queryset:
            data.append({
                'Référence': demande.reference,
                'Utilisateur': demande.utilisateur.email,
                'Document': demande.document.nom,
                'Statut': demande.get_statut_display(),
                'Montant': demande.montant_total,
                'Commission': demande.frais_commission,
                'Notaire': f"{demande.notaire.nom} {demande.notaire.prenom}" if demande.notaire else '',
                'Date création': demande.created_at,
            })
        
        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="demandes_selection.xlsx"'
        df.to_excel(response, index=False)
        return response
    export_selection_excel.short_description = "Exporter la sélection (Excel)"
    
    # Personnalisation de la vue changelist
    def changelist_view(self, request, extra_context=None):
        """Ajouter des statistiques à la vue liste"""
        extra_context = extra_context or {}
        
        # Statistiques globales
        stats = DemandesDemande.objects.aggregate(
            total=Count('id'),
            total_montant=Sum('montant_total'),
            total_commission=Sum('frais_commission'),
        )
        
        # Par statut
        par_statut = DemandesDemande.objects.values('statut').annotate(
            count=Count('id'),
            montant=Sum('montant_total')
        ).order_by('-count')
        
        extra_context['stats'] = stats
        extra_context['par_statut'] = par_statut
        
        return super().changelist_view(request, extra_context)
    
    # Personnalisation des permissions
    def has_delete_permission(self, request, obj=None):
        """Seuls les superusers peuvent supprimer"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Les staff peuvent modifier"""
        return request.user.is_staff
    
    def get_queryset(self, request):
        """Filtrer selon les permissions"""
        qs = super().get_queryset(request)
        
        # Si pas admin, ne voir que ses propres demandes assignées
        if not request.user.is_superuser and hasattr(request.user, 'notaire'):
            qs = qs.filter(notaire=request.user.notaire)
        
        # Ajouter des annotations pour le tri
        return qs.select_related('utilisateur', 'document', 'notaire')
    
    # Configuration des formulaires
    def get_form(self, request, obj=None, **kwargs):
        """Personnaliser le formulaire selon l'utilisateur"""
        form = super().get_form(request, obj, **kwargs)
        
        # Limiter les choix de notaires selon les permissions
        if not request.user.is_superuser:
            if 'notaire' in form.base_fields:
                from apps.notaires.models import NotairesNotaire
                form.base_fields['notaire'].queryset = NotairesNotaire.objects.filter(actif=True)
        
        return form

# Configuration du site admin
admin.site.site_header = "Administration de l'Ordre des Notaires"
admin.site.site_title = "Portail Administratif"
admin.site.index_title = "Tableau de bord"

# Optionnel : Personnalisation des templates
# class DemandesAdminSite(admin.AdminSite):
#     site_header = "Gestion des Demandes"
#     site_title = "Portail Demandes"
#     index_title = "Administration des demandes"