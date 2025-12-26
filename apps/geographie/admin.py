from django.contrib import admin
from .models import GeographieRegion, GeographieVille

@admin.register(GeographieRegion)
class GeographieRegionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'ordre', 'created_at', 'updated_at')
    list_filter = ('created_at', 'ordre')
    search_fields = ('nom', 'code', 'description')
    ordering = ('ordre', 'nom')
    readonly_fields = ('created_at', 'updated_at')

    def ville_count(self, obj):
        return obj.geographieville_set.count()
    ville_count.short_description = 'Nombre de Villes'

    fieldsets = (
        ('Informations', {
            'fields': ('nom', 'code', 'description', 'ordre')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(GeographieVille)

class GeographieVilleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code_postal', 'region', 'ordre', 'created_at', 'updated_at')
    list_filter = ('region', 'created_at')
    search_fields = ('nom', 'code_postal', 'region__nom')
    ordering = ('nom','region')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('region',)

    fieldsets = (
        ('Informations', {
            'fields': ('nom', 'code_postal', 'region', 'ordre')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )