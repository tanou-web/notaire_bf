from django.contrib import admin
from adminsortable2.admin import SortableAdminBase, SortableInlineAdminMixin
from .models import Evenement, EvenementChamp, Inscription, InscriptionReponse


class EvenementChampInline(SortableInlineAdminMixin, admin.TabularInline):
    model = EvenementChamp
    extra = 1
    fields = ('label', 'type', 'obligatoire', 'options', 'ordre', 'actif')
    ordering = ('ordre',)


@admin.register(Evenement)
class EvenementAdmin(SortableAdminBase, admin.ModelAdmin):
    list_display = ('titre', 'actif', 'created_at')
    inlines = [EvenementChampInline]


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'email', 'telephone', 'evenement', 'created_at')


@admin.register(InscriptionReponse)
class InscriptionReponseAdmin(admin.ModelAdmin):
    list_display = (
        'inscription',
        'champ',
        'valeur_texte',
        'valeur_nombre',
        'valeur_date',
        'valeur_fichier',
        'valeur_bool'
    )
