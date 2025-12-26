from django.contrib import admin
from .models import ContactInformations, ContactMessage


@admin.register(ContactInformations)
class ContactInformationsAdmin(admin.ModelAdmin):
	list_display = ('type', 'valeur', 'ordre', 'actif')
	list_filter = ('actif', 'type')
	search_fields = ('valeur',)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
	list_display = ('email', 'subject', 'sent', 'created_at')
	list_filter = ('sent',)
	search_fields = ('email', 'subject', 'message')
	readonly_fields = ('created_at', 'updated_at')
