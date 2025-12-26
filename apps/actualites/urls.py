from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'actualites'

router = DefaultRouter()
router.register(r'actualites', views.ActualiteViewSet, basename='actualite')

urlpatterns = [
    path('', include(router.urls)),
]