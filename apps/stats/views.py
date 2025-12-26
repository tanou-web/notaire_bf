from rest_framework import viewsets, generics, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Sum, Avg, Count, F, Q
from django.db import models
from datetime import datetime, timedelta
import json
import csv
from django.http import HttpResponse

from .models import (
    StatsVisite, PageVue, Referent, PaysVisite, 
    PeriodeActive, Appareil, Navigateur
)
from .serializers import (
    StatsVisiteSerializer, PageVueSerializer, ReferentSerializer,
    PaysVisiteSerializer, PeriodeActiveSerializer, AppareilSerializer,
    NavigateurSerializer, DashboardSerializer, RapportSerializer,
    ExportSerializer
)
from .services import StatsService
from .permissions import IsAdminOrReadOnly, CanViewStats

class StatsVisiteViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les statistiques de visites.
    
    Permet de :
    - Lister toutes les statistiques
    - Créer de nouvelles entrées
    - Récupérer/Modifier/Supprimer une entrée spécifique
    - Accéder à des endpoints personnalisés
    """
    queryset = StatsVisite.objects.all()
    serializer_class = StatsVisiteSerializer
    permission_classes = [IsAuthenticated, CanViewStats]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['date', 'est_weekend']
    search_fields = ['date', 'jour_semaine']
    ordering_fields = ['date', 'visites', 'pages_vues', 'created_at']
    ordering = ['-date']
    
    def get_queryset(self):
        """Filtre le queryset selon les paramètres de requête."""
        queryset = super().get_queryset()
        
        # Filtrage par période
        date_debut = self.request.query_params.get('date_debut')
        date_fin = self.request.query_params.get('date_fin')
        
        if date_debut and date_fin:
            queryset = queryset.filter(
                date__gte=date_debut,
                date__lte=date_fin
            )
        
        # Filtrage par nombre minimum de visites
        min_visites = self.request.query_params.get('min_visites')
        if min_visites:
            queryset = queryset.filter(visites__gte=min_visites)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def aujourdhui(self, request):
        """Récupère les statistiques du jour en cours."""
        aujourdhui = timezone.now().date()
        stats, created = StatsVisite.obtenir_ou_creer_pour_date(aujourdhui)
        serializer = self.get_serializer(stats)
        
        data = {
            'stats': serializer.data,
            'est_nouveau': created,
            'timestamp': timezone.now()
        }
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def tendances(self, request):
        """Retourne les tendances sur une période donnée."""
        jours = int(request.query_params.get('jours', 30))
        date_fin = timezone.now().date()
        date_debut = date_fin - timedelta(days=jours)
        
        tendances = StatsService.obtenir_tendances(jours)
        
        # Calcul des métriques de tendance
        if len(tendances) >= 2:
            premier_jour = tendances[0]
            dernier_jour = tendances[-1]
            
            evolution_visites = ((dernier_jour['visites'] - premier_jour['visites']) / 
                                 premier_jour['visites'] * 100) if premier_jour['visites'] > 0 else 0
            
            evolution_pages = ((dernier_jour['pages_vues'] - premier_jour['pages_vues']) / 
                               premier_jour['pages_vues'] * 100) if premier_jour['pages_vues'] > 0 else 0
        
        return Response({
            'periode': {
                'debut': date_debut,
                'fin': date_fin,
                'jours': jours
            },
            'tendances': tendances,
            'moyennes': {
                'visites': sum(t['visites'] for t in tendances) / len(tendances) if tendances else 0,
                'pages_vues': sum(t['pages_vues'] for t in tendances) / len(tendances) if tendances else 0,
            },
            'total': {
                'visites': sum(t['visites'] for t in tendances),
                'pages_vues': sum(t['pages_vues'] for t in tendances),
            }
        })
    
    @action(detail=False, methods=['get'])
    def resume_mensuel(self, request):
        """Génère un résumé mensuel."""
        mois = request.query_params.get('mois', timezone.now().month)
        annee = request.query_params.get('annee', timezone.now().year)
        
        rapport = StatsService.generer_rapport_mensuel(mois, annee)
        return Response(rapport)
    
    @action(detail=False, methods=['post'])
    def incrementer(self, request):
        """Incrémente les compteurs de visites."""
        date = request.data.get('date', timezone.now().date())
        pages_vues = request.data.get('pages_vues', 1)
        authentifie = request.data.get('authentifie', False)
        
        stats = StatsService.incrementer_visite(date, pages_vues, authentifie)
        
        if stats:
            serializer = self.get_serializer(stats)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Erreur lors de l\'incrémentation'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def pages_populaires(self, request, pk=None):
        """Liste les pages populaires pour cette date."""
        stats = self.get_object()
        pages = PageVue.objects.filter(date=stats.date).order_by('-vues')[:10]
        serializer = PageVueSerializer(pages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def top_jours(self, request):
        """Retourne les jours avec le plus de visites."""
        limit = int(request.query_params.get('limit', 10))
        top_jours = StatsVisite.objects.all().order_by('-visites')[:limit]
        serializer = self.get_serializer(top_jours, many=True)
        return Response(serializer.data)


class PageVueViewSet(viewsets.ModelViewSet):
    queryset = PageVue.objects.all()
    serializer_class = PageVueSerializer
    permission_classes = [IsAuthenticated, CanViewStats]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['date', 'url']
    search_fields = ['url', 'titre']
    
    @action(detail=False, methods=['get'])
    def top_pages(self, request):
        """Pages les plus visitées."""
        limit = int(request.query_params.get('limit', 20))
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        
        queryset = self.get_queryset()
        
        if date_debut and date_fin:
            queryset = queryset.filter(
                date__gte=date_debut,
                date__lte=date_fin
            )
        
        top_pages = queryset.values('url', 'titre').annotate(
            total_vues=Sum('vues'),
            avg_temps=Avg('temps_moyen'),
            derniere_date=models.Max('date')
        ).order_by('-total_vues')[:limit]
        
        return Response(list(top_pages))


class ReferentViewSet(viewsets.ModelViewSet):
    queryset = Referent.objects.all()
    serializer_class = ReferentSerializer
    permission_classes = [IsAuthenticated, CanViewStats]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['date', 'domaine']
    
    @action(detail=False, methods=['get'])
    def top_referents(self, request):
        """Top des sites référents."""
        limit = int(request.query_params.get('limit', 15))
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        
        queryset = self.get_queryset()
        
        if date_debut and date_fin:
            queryset = queryset.filter(
                date__gte=date_debut,
                date__lte=date_fin
            )
        
        top_referents = queryset.values('domaine').annotate(
            total_visites=Sum('visites'),
            premier_date=models.Min('date'),
            dernier_date=models.Max('date')
        ).order_by('-total_visites')[:limit]
        
        return Response(list(top_referents))


class PaysVisiteViewSet(viewsets.ModelViewSet):
    queryset = PaysVisite.objects.all()
    serializer_class = PaysVisiteSerializer
    permission_classes = [IsAuthenticated, CanViewStats]
    
    @action(detail=False, methods=['get'])
    def distribution(self, request):
        """Distribution géographique des visites."""
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        
        queryset = self.get_queryset()
        
        if date_debut and date_fin:
            queryset = queryset.filter(
                date__gte=date_debut,
                date__lte=date_fin
            )
        
        distribution = queryset.values('pays', 'code_pays').annotate(
            total_visites=Sum('visites')
        ).order_by('-total_visites')
        
        total = sum(item['total_visites'] for item in distribution)
        
        # Ajouter des pourcentages
        for item in distribution:
            item['pourcentage'] = round((item['total_visites'] / total * 100), 2) if total > 0 else 0
        
        return Response({
            'distribution': list(distribution),
            'total_pays': len(distribution),
            'total_visites': total
        })


class PeriodeActiveViewSet(viewsets.ModelViewSet):
    queryset = PeriodeActive.objects.all()
    serializer_class = PeriodeActiveSerializer
    permission_classes = [IsAuthenticated, CanViewStats]
    
    @action(detail=False, methods=['get'])
    def heures_actives(self, request):
        """Heures les plus actives de la journée."""
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        
        queryset = self.get_queryset()
        
        if date_debut and date_fin:
            queryset = queryset.filter(
                date__gte=date_debut,
                date__lte=date_fin
            )
        
        heures_actives = queryset.values('heure').annotate(
            total_visites=Sum('visites')
        ).order_by('heure')
        
        # Formater les heures
        formatted_data = []
        for item in heures_actives:
            formatted_data.append({
                'heure': f"{item['heure']}:00",
                'visites': item['total_visites']
            })
        
        return Response(formatted_data)


class AppareilViewSet(viewsets.ModelViewSet):
    queryset = Appareil.objects.all()
    serializer_class = AppareilSerializer
    permission_classes = [IsAuthenticated, CanViewStats]


class NavigateurViewSet(viewsets.ModelViewSet):
    queryset = Navigateur.objects.all()
    serializer_class = NavigateurSerializer
    permission_classes = [IsAuthenticated, CanViewStats]


class DashboardView(generics.GenericAPIView):
    """Vue pour le tableau de bord des statistiques."""
    permission_classes = [IsAuthenticated, CanViewStats]
    serializer_class = DashboardSerializer
    
    def get(self, request):
        periode = request.query_params.get('periode', '30j')
        
        # Déterminer la période
        date_fin = timezone.now().date()
        if periode == '7j':
            date_debut = date_fin - timedelta(days=7)
        elif periode == '30j':
            date_debut = date_fin - timedelta(days=30)
        elif periode == '90j':
            date_debut = date_fin - timedelta(days=90)
        else:
            date_debut = date_fin - timedelta(days=30)
        
        # Récupérer les données
        stats_periode = StatsVisite.objects.filter(
            date__gte=date_debut,
            date__lte=date_fin
        )
        
        # Calculer les métriques
        total_visites = stats_periode.aggregate(total=Sum('visites'))['total'] or 0
        total_pages = stats_periode.aggregate(total=Sum('pages_vues'))['total'] or 0
        moyenne_visites = stats_periode.aggregate(moyenne=Avg('visites'))['moyenne'] or 0
        moyenne_pages_par_visite = stats_periode.aggregate(
            moyenne=Avg('pages_vues') / Avg('visites')
        )['moyenne'] or 0
        
        # Dernier jour
        dernier_jour = StatsVisite.objects.filter(
            date__gte=date_debut,
            date__lte=date_fin
        ).order_by('-date').first()
        
        # Top pages
        top_pages = PageVue.objects.filter(
            date__gte=date_debut,
            date__lte=date_fin
        ).values('url', 'titre').annotate(
            vues=Sum('vues')
        ).order_by('-vues')[:5]
        
        # Top pays
        top_pays = PaysVisite.objects.filter(
            date__gte=date_debut,
            date__lte=date_fin
        ).values('pays', 'code_pays').annotate(
            visites=Sum('visites')
        ).order_by('-visites')[:5]
        
        data = {
            'periode': {
                'debut': date_debut,
                'fin': date_fin,
                'label': periode
            },
            'metriques': {
                'total_visites': total_visites,
                'total_pages_vues': total_pages,
                'visites_moyennes': round(moyenne_visites, 2),
                'pages_par_visite': round(moyenne_pages_par_visite, 2),
                'visites_dernier_jour': dernier_jour.visites if dernier_jour else 0,
                'pages_dernier_jour': dernier_jour.pages_vues if dernier_jour else 0,
            },
            'top_pages': list(top_pages),
            'top_pays': list(top_pays),
            'derniere_mise_a_jour': timezone.now()
        }
        
        return Response(data)


class TendancesView(generics.GenericAPIView):
    """Analyse des tendances temporelles."""
    permission_classes = [IsAuthenticated, CanViewStats]
    
    def get(self, request):
        jours = int(request.query_params.get('jours', 30))
        metrique = request.query_params.get('metrique', 'visites')
        
        date_fin = timezone.now().date()
        date_debut = date_fin - timedelta(days=jours)
        
        # Récupérer les données par jour
        stats = StatsVisite.objects.filter(
            date__gte=date_debut,
            date__lte=date_fin
        ).order_by('date')
        
        # Préparer les données pour les graphiques
        labels = []
        data_points = []
        
        for stat in stats:
            labels.append(stat.date.strftime('%d/%m'))
            
            if metrique == 'visites':
                data_points.append(stat.visites)
            elif metrique == 'pages_vues':
                data_points.append(stat.pages_vues)
            elif metrique == 'pages_par_visite':
                data_points.append(stat.pages_par_visite)
            elif metrique == 'duree_moyenne':
                data_points.append(stat.duree_moyenne)
            elif metrique == 'taux_rebond':
                data_points.append(stat.taux_rebond)
        
        # Calculer les tendances
        if len(data_points) > 1:
            premier = data_points[0]
            dernier = data_points[-1]
            evolution = ((dernier - premier) / premier * 100) if premier > 0 else 0
        else:
            evolution = 0
        
        return Response({
            'periode': f"{date_debut} à {date_fin}",
            'jours': jours,
            'metrique': metrique,
            'labels': labels,
            'data': data_points,
            'evolution': round(evolution, 2),
            'moyenne': round(sum(data_points) / len(data_points) if data_points else 0, 2),
            'maximum': max(data_points) if data_points else 0,
            'minimum': min(data_points) if data_points else 0
        })


class GenererRapportView(generics.GenericAPIView):
    """Génération de rapports PDF/Excel."""
    permission_classes = [IsAuthenticated, CanViewStats]
    serializer_class = RapportSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            format_rapport = data.get('format', 'pdf')
            date_debut = data.get('date_debut')
            date_fin = data.get('date_fin')
            type_rapport = data.get('type_rapport', 'complet')
            
            # Ici, vous intégreriez votre logique de génération de rapport
            # Par exemple, utiliser ReportLab pour PDF ou openpyxl pour Excel
            
            # Pour l'exemple, on retourne un JSON simulé
            rapport_data = {
                'titre': f"Rapport statistiques {date_debut} à {date_fin}",
                'periode': f"{date_debut} - {date_fin}",
                'date_generation': timezone.now().isoformat(),
                'format': format_rapport,
                'type': type_rapport,
                'lien_telechargement': f'/api/stats/export/rapport_{date_debut}_{date_fin}.{format_rapport}'
            }
            
            return Response(rapport_data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExportStatsView(generics.GenericAPIView):
    """Export des données statistiques."""
    permission_classes = [IsAuthenticated, CanViewStats]
    
    def get(self, request):
        format_export = request.query_params.get('format', 'json')
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        
        # Filtrer les données
        queryset = StatsVisite.objects.all()
        if date_debut and date_fin:
            queryset = queryset.filter(
                date__gte=date_debut,
                date__lte=date_fin
            )
        
        if format_export == 'csv':
            # Générer un CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="stats_{date_debut}_{date_fin}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Date', 'Visites', 'Pages vues', 'Durée moyenne', 'Taux rebond'])
            
            for stat in queryset:
                writer.writerow([
                    stat.date,
                    stat.visites,
                    stat.pages_vues,
                    stat.duree_moyenne,
                    stat.taux_rebond
                ])
            
            return response
        
        elif format_export == 'excel':
            # Pour Excel, vous pourriez utiliser openpyxl ou pandas
            # Ici un exemple simplifié
            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = f'attachment; filename="stats_{date_debut}_{date_fin}.xlsx"'
            
            # Utiliser pandas pour générer Excel
            import pandas as pd
            data = list(queryset.values('date', 'visites', 'pages_vues', 'duree_moyenne', 'taux_rebond'))
            df = pd.DataFrame(data)
            
            # Sauvegarder dans un buffer
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Statistiques', index=False)
            
            response.write(output.getvalue())
            return response
        
        else:  # JSON par défaut
            serializer = StatsVisiteSerializer(queryset, many=True)
            return Response(serializer.data)


class SynchroniserStatsView(generics.GenericAPIView):
    """Synchronisation avec Google Analytics, Matomo, etc."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        source = request.data.get('source', 'google_analytics')
        date_debut = request.data.get('date_debut')
        date_fin = request.data.get('date_fin')
        
        # Ici, vous intégreriez l'API de la source externe
        # Pour l'exemple, on simule une synchronisation
        
        resultats = {
            'source': source,
            'periode': f"{date_debut} à {date_fin}",
            'statut': 'synchronisation_en_cours',
            'taches': [
                {'nom': 'Récupération données visites', 'statut': 'terminé'},
                {'nom': 'Import pages vues', 'statut': 'en_cours'},
                {'nom': 'Mise à jour référents', 'statut': 'en_attente'}
            ],
            'date_debut_sync': timezone.now().isoformat()
        }
        
        return Response(resultats)


class AlertesView(generics.GenericAPIView):
    """Gestion des alertes (anomalies de trafic, etc.)."""
    permission_classes = [IsAuthenticated, CanViewStats]
    
    def get(self, request):
        # Détecter les anomalies (ex: chute soudaine du trafic)
        aujourdhui = timezone.now().date()
        hier = aujourdhui - timedelta(days=1)
        
        stats_aujourdhui = StatsVisite.obtenir_ou_creer_pour_date(aujourdhui)[0]
        stats_hier = StatsVisite.objects.filter(date=hier).first()
        
        alertes = []
        
        if stats_hier:
            # Vérifier les variations importantes
            if stats_hier.visites > 0:
                variation = ((stats_aujourdhui.visites - stats_hier.visites) / 
                            stats_hier.visites * 100)
                
                if variation < -50:  # Chute de plus de 50%
                    alertes.append({
                        'type': 'chute_trafic',
                        'severite': 'haute',
                        'message': f'Chute importante du trafic: {variation:.1f}%',
                        'date': aujourdhui,
                        'details': {
                            'visites_hier': stats_hier.visites,
                            'visites_aujourdhui': stats_aujourdhui.visites,
                            'variation': variation
                        }
                    })
        
        return Response({
            'alertes': alertes,
            'nombre_alertes': len(alertes),
            'date_verification': timezone.now().isoformat()
        })