from django.contrib import admin
from .models import ConseilsConseildujour

@admin.register(ConseilsConseildujour)
class ConseilDuJourAdmin(admin.ModelAdmin):
	list_display = ('date', 'actif')
	list_filter = ('actif',)
	search_fields = ('conseil',)
	readonly_fields = ('created_at', 'updated_at')
