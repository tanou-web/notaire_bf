from django.contrib import admin
from .models import PartenairesPartenaire


@admin.register(PartenairesPartenaire)
class PartenaireAdmin(admin.ModelAdmin):
	list_display = ('nom', 'type_partenaire', 'ordre', 'actif')
	list_filter = ('type_partenaire', 'actif')
	search_fields = ('nom', 'description')
	readonly_fields = ('created_at', 'updated_at')
