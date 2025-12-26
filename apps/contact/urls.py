from django.urls import path
from .views import ContactInformationListView, ContactMessageCreateView

urlpatterns = [
	path('info/', ContactInformationListView.as_view(), name='contact-info'),
	path('form/', ContactMessageCreateView.as_view(), name='contact-form'),
]
