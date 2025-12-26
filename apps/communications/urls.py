from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContactAPIView, CommunicationsEmailLogViewSet

router = DefaultRouter()
router.register(r'email-logs', CommunicationsEmailLogViewSet, basename='email-log')

urlpatterns = [
    path('contact/', ContactAPIView.as_view(), name='communications-contact'),
    path('', include(router.urls)),
]
