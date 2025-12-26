from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'documents'

router = DefaultRouter()
router.register(r'documents', views.DocumentViewSet, basename='document')
router.register(r'textes-legaux', views.TexteLegalViewSet, basename='textelegal')

# URL supplémentaires pour les actions custom (si nécessaire)
custom_urlpatterns = [
    # Les actions custom sont déjà incluses via les ViewSets
    # Ex: /api/documents/documents/actifs/ est déjà disponible via DocumentViewSet
]

urlpatterns = [
    path('', include(router.urls)),
] + custom_urlpatterns