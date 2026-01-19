from django.contrib import admin
from .models import Evenement, Inscription

@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ('titre', 'date_debut', 'lieu', 'prix', 'actif', 'statut')
    list_filter = ('actif', 'date_debut', 'statut')
    search_fields = ('titre', 'lieu')
    fields = ('titre', 'description', 'date_debut', 'date_fin', 'lieu', 'prix', 'image', 'actif', 'statut')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'evenement', 'qualite', 'statut_paiement', 'created_at')
    list_filter = ('statut_paiement', 'qualite', 'evenement')
    search_fields = ('nom', 'prenom', 'email', 'telephone')
    readonly_fields = ('created_at', 'updated_at')
