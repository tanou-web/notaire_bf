from rest_framework.routers import DefaultRouter
from .views import NotaireViewSet

router = DefaultRouter()
router.register(r'notaires', NotaireViewSet, basename='notaire')

urlpatterns = router.urls
