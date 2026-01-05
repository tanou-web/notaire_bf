from django.contrib import admin
from django.db.models import Count, Sum, Avg
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import CoreConfiguration, CorePage


from django.contrib import admin
from .models import CoreConfiguration

@admin.register(CoreConfiguration)
class CoreConfigurationAdmin(admin.ModelAdmin):
    list_display = ('cle', 'valeur', 'description', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')  # tu peux filtrer sur les dates
    search_fields = ('cle', 'description')
    ordering = ('cle',)


@admin.register(CorePage)
class CorePageAdmin(admin.ModelAdmin):
    list_display = ('titre', 'slug', 'publie', 'ordre', 'date_publication', 'auteur', 'vues_count')
    list_filter = ('publie', 'date_publication', 'auteur')
    search_fields = ('titre', 'slug', 'contenu')
    prepopulated_fields = {'slug': ('titre',)}
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Informations générales', {
            'fields': ('titre', 'slug', 'auteur')
        }),
        ('Contenu', {
            'fields': ('contenu', 'resume'),
            'classes': ('collapse',)
        }),
        ('Publication', {
            'fields': ('publie', 'date_publication', 'ordre')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'image_principale'),
            'classes': ('collapse',)
        }),
        ('Template', {
            'fields': ('template',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def vues_count(self, obj):
        return "N/A"  # À implémenter avec un champ vues
    vues_count.short_description = "Vues"


# Dashboard personnalisé pour l'administration
class NotaireBFDashboard(admin.AdminSite):
    site_header = "🏛️ Notaire BF - Administration"
    site_title = "Notaire BF Admin"
    index_title = "Tableau de bord - Ordre des Notaires Burkina Faso"

    def get_app_list(self, request):
        """
        Personnalisation de la liste des applications dans l'admin
        """
        app_list = super().get_app_list(request)

        # Ajouter des statistiques personnalisées
        for app in app_list:
            if app['app_label'] == 'demandes':
                # Statistiques des demandes
                from apps.demandes.models import Demande
                total_demandes = Demande.objects.count()
                demandes_en_cours = Demande.objects.filter(statut='en_cours').count()
                demandes_finalisees = Demande.objects.filter(statut='finalise').count()

                app['stats'] = {
                    'total': total_demandes,
                    'en_cours': demandes_en_cours,
                    'finalisees': demandes_finalisees
                }

            elif app['app_label'] == 'paiements':
                # Statistiques des paiements
                from apps.paiements.models import Transaction
                from django.db.models import Sum

                total_transactions = Transaction.objects.count()
                montant_total = Transaction.objects.filter(statut='reussi').aggregate(
                    total=Sum('montant')
                )['total'] or 0

                app['stats'] = {
                    'total': total_transactions,
                    'montant_total': f"{montant_total:,.0f} XOF"
                }

            elif app['app_label'] == 'utilisateurs':
                # Statistiques des utilisateurs
                from django.contrib.auth import get_user_model
                User = get_user_model()

                total_users = User.objects.count()
                notaires = User.objects.exclude(notaires__isnull=True).count()  # À ajuster selon le modèle

                app['stats'] = {
                    'total': total_users,
                    'notaires': notaires
                }

        return app_list

    def index(self, request, extra_context=None):
        """
        Page d'accueil personnalisée avec statistiques
        """
        extra_context = extra_context or {}

        # Statistiques générales
        from apps.demandes.models import Demande
        from apps.paiements.models import Transaction
        from apps.stats.models import Visite
        from django.contrib.auth import get_user_model
        from django.db.models import Count, Sum

        User = get_user_model()

        # Métriques principales
        stats = {
            'demandes_total': Demande.objects.count(),
            'demandes_en_cours': Demande.objects.filter(statut='en_cours').count(),
            'transactions_total': Transaction.objects.count(),
            'transactions_reussies': Transaction.objects.filter(statut='reussi').count(),
            'montant_total': Transaction.objects.filter(statut='reussi').aggregate(
                total=Sum('montant')
            )['total'] or 0,
            'utilisateurs_total': User.objects.count(),
            'visites_total': Visite.objects.count(),
        }

        # Évolution sur les 7 derniers jours
        last_week = timezone.now() - timezone.timedelta(days=7)

        demandes_semaine = Demande.objects.filter(created_at__gte=last_week).count()
        transactions_semaine = Transaction.objects.filter(created_at__gte=last_week).count()

        stats.update({
            'demandes_semaine': demandes_semaine,
            'transactions_semaine': transactions_semaine,
        })

        # Alertes importantes
        alerts = []

        # Demandes urgentes
        demandes_urgentes = Demande.objects.filter(urgence='urgent', statut__in=['attente_formulaire', 'en_cours'])
        if demandes_urgentes.exists():
            alerts.append({
                'type': 'warning',
                'message': f"{demandes_urgentes.count()} demande(s) urgente(s) en attente",
                'url': reverse('admin:demandes_demande_changelist') + f'?urgence__exact=urgent'
            })

        # Transactions échouées
        transactions_echouees = Transaction.objects.filter(statut='echoue')
        if transactions_echouees.exists():
            alerts.append({
                'type': 'error',
                'message': f"{transactions_echouees.count()} transaction(s) échouée(s)",
                'url': reverse('admin:paiements_transaction_changelist') + f'?statut__exact=echoue'
            })

        extra_context.update({
            'stats': stats,
            'alerts': alerts,
            'recent_activity': self.get_recent_activity()
        })

        return super().index(request, extra_context)

    def get_recent_activity(self):
        """
        Récupère les activités récentes pour le dashboard
        """
        activities = []

        # Demandes récentes
        from apps.demandes.models import Demande
        recent_demandes = Demande.objects.select_related('utilisateur').order_by('-created_at')[:5]
        for demande in recent_demandes:
            activities.append({
                'type': 'demande',
                'icon': '📄',
                'message': f"Demande #{demande.numero_reference} créée par {demande.utilisateur.get_full_name() if demande.utilisateur else 'Anonyme'}",
                'timestamp': demande.created_at,
                'url': reverse('admin:demandes_demande_change', args=[demande.pk])
            })

        # Transactions récentes
        from apps.paiements.models import Transaction
        recent_transactions = Transaction.objects.select_related('utilisateur').order_by('-date_creation')[:5]
        for transaction in recent_transactions:
            activities.append({
                'type': 'transaction',
                'icon': '💳',
                'message': f"Transaction {transaction.reference_interne}: {transaction.montant} XOF ({transaction.get_statut_display()})",
                'timestamp': transaction.date_creation,
                'url': reverse('admin:paiements_transaction_change', args=[transaction.pk])
            })

        # Trier par timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:10]  # Top 10


# Instance personnalisée du site admin
admin_site = NotaireBFDashboard(name='notaire_bf_admin')

# Enregistrer les modèles dans le site personnalisé
admin_site.register(CoreConfiguration, CoreConfigurationAdmin)
admin_site.register(CorePage, CorePageAdmin)

