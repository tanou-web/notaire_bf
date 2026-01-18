"""
URL configuration for notaires_bf project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.urls import re_path
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
#Documentation Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="Notaires BF API",
        default_version='v1',
        description="API documentation for Notaires BF",
        contact=openapi.Contact(email="contact@notairesbf.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,   
        permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    #admin
    path('admin/', admin.site.urls),
    #Api 
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    #JWT Auth
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    #API Applications
    path('api/auth/', include('apps.utilisateurs.urls')),
    path('api/geographie/', include('apps.geographie.urls')),
    path('api/notaires/', include('apps.notaires.urls')),
    path('api/documents/', include('apps.documents.urls')),
    path('api/demandes/', include('apps.demandes.urls')),
    path('api/paiements/', include('apps.paiements.urls')),
    path('api/actualites/', include('apps.actualites.urls')),
    path('api/partenaires/', include('apps.partenaires.urls')),
    path('api/conseils/', include('apps.conseils.urls')),
    path('api/organisation/', include('apps.organisation.urls')),
    path('api/contact/', include('apps.contact.urls')),
    path('api/ventes/', include('apps.ventes.urls')),
    path('api/stats/', include('apps.stats.urls')),
    path('api/communications/', include('apps.communications.urls')),
    path('api/audit/', include('apps.audit.urls')),
    path('api/system/', include('apps.system.urls')),
    path('api/core/', include('apps.core.urls')),  
    path('api/evenements/', include('apps.evenements.urls')),
    path('api/admin/', include('apps.utilisateurs.urls')),  # ✅ AJOUTEZ CETTE LIGNE

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)    
       
    urlpatterns += [
        re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0),
            name='schema-json'),
    ]   

