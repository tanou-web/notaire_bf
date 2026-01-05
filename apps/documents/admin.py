from django.contrib import admin
from .models import DocumentsDocument, DocumentsTextelegal
from django.utils.html import format_html

@admin.register(DocumentsDocument)
class DocumentsDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'reference', 'nom', 'prix_formate','delai_affichage', 'actif', 'created_at', 'updated_at','fichier_lien')
    list_filter = ('actif', 'delai_heures', 'created_at', 'updated_at')
    search_fields = ('reference', 'nom', 'description')
    list_editable = ('actif',)
    ordering = ('nom', 'reference')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Informations de base', {
            'fields': ('reference', 'nom', 'description')
        }),
        ('Tarification et délai', {
            'fields': ('prix', 'delai_heures')
        }),
        ('Fichier', {
            'fields': ('fichier',)
        }),
        ('Dates',{
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def prix_formate(self, obj):
        return f"{obj.prix:,.0f} FCFA".replace(',', ' ')
    prix_formate.short_description = 'Prix (FCFA)'

    def delai_affichage(self, obj):
        delai_heures_display = obj.get_delai_heures_display()
        return delai_heures_display if delai_heures_display else 'Non défini'
    delai_affichage.short_description = 'Délai'


    def fichier_lien(self, obj):
        if obj.fichier:
            return format_html('<a href="{}" target="_blank">Télécharger</a>', obj.fichier.url)
        return "Aucun fichier"
    fichier_lien.short_description = 'Fichier PDF'

@admin.register(DocumentsTextelegal)
class DocumentsTextelegalAdmin(admin.ModelAdmin):
    list_display = ('id', 'type_texte_display', 'reference', 'titre', 'fichier_lien', 'date_publication', 'ordre', 'created_at')
    list_filter = ('type_texte', 'date_publication', 'created_at')
    search_fields = ('reference', 'titre', 'type_texte')
    ordering = ('type_texte', 'ordre', 'titre')
    readonly_fields = ('created_at', 'updated_at') 
    fieldsets = (
        ('Informations', {
            'fields': ('type_texte', 'reference', 'titre')
        }),
        ('Fichier et date', {
            'fields': ('fichier', 'date_publication'),
        }),
        ('Ordre d\'affichage et dates', {
            'fields': ('ordre', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def type_texte_display(self, obj):
        return obj.get_type_texte_display()
    type_texte_display.short_description = 'Type de Texte'

    def fichier_lien(self, obj):
        if obj.fichier:
            return format_html('<a href="{}" target="_blank">Télécharger</a>', obj.fichier.url)
        return "Aucun fichier"
    fichier_lien.short_description = 'Fichier'
