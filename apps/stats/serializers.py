from rest_framework import serializers
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, timedelta
import re

from .models import (
    StatsVisite, PageVue, Referent, PaysVisite, 
    PeriodeActive, Appareil, Navigateur
)


class StatsVisiteSerializer(serializers.ModelSerializer):
    """Serializer pour les statistiques de visites."""
    
    # Champs calculés en lecture seule
    pages_par_visite = serializers.SerializerMethodField(read_only=True)
    duree_totale = serializers.SerializerMethodField(read_only=True)
    trafic_total = serializers.SerializerMethodField(read_only=True)
    jour_semaine = serializers.SerializerMethodField(read_only=True)
    est_weekend = serializers.SerializerMethodField(read_only=True)
    
    # Champs pour les validations
    date = serializers.DateField(
        validators=[
            UniqueValidator(
                queryset=StatsVisite.objects.all(),
                message='Une entrée existe déjà pour cette date'
            )
        ]
    )
    
    visites = serializers.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Nombre total de visites uniques"
    )
    
    pages_vues = serializers.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Nombre total de pages consultées"
    )
    
    taux_rebond = serializers.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        required=False,
        help_text="Taux de rebond en pourcentage (0-100)"
    )
    
    duree_moyenne = serializers.FloatField(
        validators=[MinValueValidator(0)],
        required=False,
        help_text="Durée moyenne des visites en minutes"
    )
    
    class Meta:
        model = StatsVisite
        fields = [
            'id', 'date', 'visites', 'pages_vues', 'visites_authentifiees',
            'duree_moyenne', 'taux_rebond', 'trafic_direct', 'trafic_reference',
            'trafic_recherche', 'trafic_social', 'created_at', 'updated_at',
            'pages_par_visite', 'duree_totale', 'trafic_total', 'jour_semaine', 'est_weekend'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_pages_par_visite(self, obj):
        """Calcule le nombre moyen de pages par visite."""
        return obj.pages_par_visite
    
    def get_duree_totale(self, obj):
        """Calcule la durée totale passée sur le site."""
        return obj.duree_totale
    
    def get_trafic_total(self, obj):
        """Calcule le trafic total de toutes sources."""
        return obj.trafic_total
    
    def get_jour_semaine(self, obj):
        """Retourne le jour de la semaine en français."""
        return obj.jour_semaine
    
    def get_est_weekend(self, obj):
        """Détermine si la date est un weekend."""
        return obj.est_weekend
    
    def validate(self, data):
        """Validation croisée des données."""
        # Vérifier que la date n'est pas dans le futur
        if 'date' in data and data['date'] > timezone.now().date():
            raise serializers.ValidationError({
                'date': 'La date ne peut pas être dans le futur'
            })
        
        # Vérifier la cohérence entre pages_vues et visites
        if 'pages_vues' in data and 'visites' in data:
            if data['pages_vues'] < data['visites']:
                raise serializers.ValidationError({
                    'pages_vues': 'Le nombre de pages vues doit être supérieur ou égal au nombre de visites'
                })
        
        # Vérifier que les totaux de trafic sont cohérents avec les visites
        trafic_fields = ['trafic_direct', 'trafic_reference', 'trafic_recherche', 'trafic_social']
        total_trafic = sum(data.get(field, 0) for field in trafic_fields)
        
        if 'visites' in data and total_trafic > data['visites'] * 1.5:
            raise serializers.ValidationError({
                'trafic_total': f'Le trafic total ({total_trafic}) semble trop élevé par rapport aux visites ({data.get("visites", 0)})'
            })
        
        return data
    
    def create(self, validated_data):
        """Création avec génération automatique de certaines données."""
        # Générer le taux de rebond si non fourni
        if 'taux_rebond' not in validated_data:
            validated_data['taux_rebond'] = self._calculer_taux_rebond_par_defaut(
                validated_data.get('visites', 0),
                validated_data.get('pages_vues', 0)
            )
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Mise à jour avec calculs automatiques."""
        # Si les visites ou pages changent, recalculer le taux de rebond
        if ('visites' in validated_data or 'pages_vues' in validated_data) and 'taux_rebond' not in validated_data:
            visites = validated_data.get('visites', instance.visites)
            pages_vues = validated_data.get('pages_vues', instance.pages_vues)
            validated_data['taux_rebond'] = self._calculer_taux_rebond_par_defaut(visites, pages_vues)
        
        return super().update(instance, validated_data)
    
    def _calculer_taux_rebond_par_defaut(self, visites, pages_vues):
        """Calcule un taux de rebond par défaut basé sur les données."""
        if visites == 0:
            return 0.0
        
        # Estimation basique: si pages_vues est proche de visites, taux de rebond élevé
        ratio = pages_vues / visites
        if ratio <= 1.2:
            return 70.0  # Haut taux de rebond
        elif ratio <= 2.0:
            return 50.0  # Moyen
        else:
            return 30.0  # Bas


class PageVueSerializer(serializers.ModelSerializer):
    """Serializer pour les statistiques de pages vues."""
    
    url = serializers.CharField(
        max_length=500,
        help_text="URL de la page"
    )
    
    titre = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text="Titre de la page"
    )
    
    vues = serializers.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Nombre de vues de la page"
    )
    
    temps_moyen = serializers.FloatField(
        validators=[MinValueValidator(0)],
        help_text="Temps moyen passé sur la page en secondes"
    )
    
    # Champs calculés
    pourcentage_total = serializers.SerializerMethodField(read_only=True)
    url_courte = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = PageVue
        fields = [
            'id', 'date', 'url', 'titre', 'vues', 'temps_moyen',
            'pourcentage_total', 'url_courte', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        validators = [
            UniqueTogetherValidator(
                queryset=PageVue.objects.all(),
                fields=['date', 'url'],
                message='Une entrée existe déjà pour cette URL et cette date'
            )
        ]
    
    def get_pourcentage_total(self, obj):
        """Calcule le pourcentage que représente cette page par rapport au total."""
        try:
            total_vues_jour = PageVue.objects.filter(
                date=obj.date
            ).aggregate(total=Sum('vues'))['total'] or 0
            
            if total_vues_jour > 0:
                return round((obj.vues / total_vues_jour) * 100, 2)
        except:
            pass
        return 0.0
    
    def get_url_courte(self, obj):
        """Retourne une version raccourcie de l'URL pour l'affichage."""
        if len(obj.url) > 50:
            return obj.url[:47] + '...'
        return obj.url
    
    def validate_url(self, value):
        """Valide que l'URL est au format correct."""
        # Vérification basique de l'URL
        if not re.match(r'^https?://', value) and not value.startswith('/'):
            raise serializers.ValidationError(
                "L'URL doit commencer par http://, https:// ou /"
            )
        
        # Limiter la longueur pour la base de données
        if len(value) > 500:
            raise serializers.ValidationError(
                "L'URL ne doit pas dépasser 500 caractères"
            )
        
        return value
    
    def validate(self, data):
        """Validation croisée des données."""
        # Vérifier que la date n'est pas dans le futur
        if 'date' in data and data['date'] > timezone.now().date():
            raise serializers.ValidationError({
                'date': 'La date ne peut pas être dans le futur'
            })
        
        # Vérifier la cohérence du temps moyen
        if 'temps_moyen' in data and data['temps_moyen'] > 3600:  # 1 heure
            raise serializers.ValidationError({
                'temps_moyen': 'Le temps moyen ne peut pas dépasser 1 heure (3600 secondes)'
            })
        
        return data


class ReferentSerializer(serializers.ModelSerializer):
    """Serializer pour les sites référents."""
    
    domaine = serializers.CharField(
        max_length=200,
        help_text="Domaine du site référent"
    )
    
    url = serializers.CharField(
        max_length=500,
        help_text="URL complète de la page référente"
    )
    
    visites = serializers.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Nombre de visites provenant de ce référent"
    )
    
    # Champs calculés
    domaine_nettoye = serializers.SerializerMethodField(read_only=True)
    pourcentage_total = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Referent
        fields = [
            'id', 'date', 'domaine', 'url', 'visites',
            'domaine_nettoye', 'pourcentage_total', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        validators = [
            UniqueTogetherValidator(
                queryset=Referent.objects.all(),
                fields=['date', 'domaine'],
                message='Une entrée existe déjà pour ce domaine et cette date'
            )
        ]
    
    def get_domaine_nettoye(self, obj):
        """Nettoie le domaine pour l'affichage."""
        # Retirer www., http://, https://
        domaine = obj.domaine.lower()
        domaine = domaine.replace('www.', '').replace('http://', '').replace('https://', '')
        return domaine.split('/')[0]  # Garder seulement le domaine principal
    
    def get_pourcentage_total(self, obj):
        """Calcule le pourcentage de trafic provenant de ce référent."""
        try:
            total_referents_jour = Referent.objects.filter(
                date=obj.date
            ).aggregate(total=Sum('visites'))['total'] or 0
            
            if total_referents_jour > 0:
                return round((obj.visites / total_referents_jour) * 100, 2)
        except:
            pass
        return 0.0
    
    def validate_domaine(self, value):
        """Valide le domaine."""
        # Vérifier que c'est un domaine valide
        if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise serializers.ValidationError(
                "Le format du domaine est invalide"
            )
        
        return value.lower()  # Toujours stocker en minuscules
    
    def validate(self, data):
        """Validation croisée."""
        if 'date' in data and data['date'] > timezone.now().date():
            raise serializers.ValidationError({
                'date': 'La date ne peut pas être dans le futur'
            })
        
        return data


class PaysVisiteSerializer(serializers.ModelSerializer):
    """Serializer pour les statistiques géographiques."""
    
    pays = serializers.CharField(
        max_length=100,
        help_text="Nom du pays"
    )
    
    code_pays = serializers.CharField(
        max_length=2,
        min_length=2,
        help_text="Code ISO du pays (2 lettres)"
    )
    
    visites = serializers.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Nombre de visites provenant de ce pays"
    )
    
    # Champs calculés
    drapeau_url = serializers.SerializerMethodField(read_only=True)
    pourcentage_total = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = PaysVisite
        fields = [
            'id', 'date', 'pays', 'code_pays', 'visites',
            'drapeau_url', 'pourcentage_total', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        validators = [
            UniqueTogetherValidator(
                queryset=PaysVisite.objects.all(),
                fields=['date', 'pays'],
                message='Une entrée existe déjà pour ce pays et cette date'
            )
        ]
    
    def get_drapeau_url(self, obj):
        """Génère une URL de drapeau basée sur le code pays."""
        # Utiliser un service de drapeaux (ex: flagcdn.com)
        return f"https://flagcdn.com/16x12/{obj.code_pays.lower()}.png"
    
    def get_pourcentage_total(self, obj):
        """Calcule le pourcentage de trafic provenant de ce pays."""
        try:
            total_pays_jour = PaysVisite.objects.filter(
                date=obj.date
            ).aggregate(total=Sum('visites'))['total'] or 0
            
            if total_pays_jour > 0:
                return round((obj.visites / total_pays_jour) * 100, 2)
        except:
            pass
        return 0.0
    
    def validate_code_pays(self, value):
        """Valide le code pays."""
        # Vérifier que c'est un code à 2 lettres
        if not re.match(r'^[A-Z]{2}$', value):
            raise serializers.ValidationError(
                "Le code pays doit être composé de 2 lettres majuscules (ex: FR, US)"
            )
        
        return value
    
    def validate(self, data):
        """Validation croisée."""
        if 'date' in data and data['date'] > timezone.now().date():
            raise serializers.ValidationError({
                'date': 'La date ne peut pas être dans le futur'
            })
        
        # Vérifier la cohérence entre pays et code pays
        # (Ici, on pourrait ajouter une vérification contre une liste de pays valides)
        
        return data


class PeriodeActiveSerializer(serializers.ModelSerializer):
    """Serializer pour les périodes d'activité."""
    
    heure = serializers.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        help_text="Heure de la journée (0-23)"
    )
    
    visites = serializers.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Nombre de visites à cette heure"
    )
    
    # Champs calculés
    heure_formattee = serializers.SerializerMethodField(read_only=True)
    pourcentage_jour = serializers.SerializerMethodField(read_only=True)
    periode_jour = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = PeriodeActive
        fields = [
            'id', 'date', 'heure', 'visites', 'heure_formattee',
            'pourcentage_jour', 'periode_jour', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        validators = [
            UniqueTogetherValidator(
                queryset=PeriodeActive.objects.all(),
                fields=['date', 'heure'],
                message='Une entrée existe déjà pour cette heure et cette date'
            )
        ]
    
    def get_heure_formattee(self, obj):
        """Formate l'heure pour l'affichage."""
        return f"{obj.heure:02d}:00"
    
    def get_pourcentage_jour(self, obj):
        """Calcule le pourcentage de visites à cette heure par rapport au total de la journée."""
        try:
            total_visites_jour = PeriodeActive.objects.filter(
                date=obj.date
            ).aggregate(total=Sum('visites'))['total'] or 0
            
            if total_visites_jour > 0:
                return round((obj.visites / total_visites_jour) * 100, 2)
        except:
            pass
        return 0.0
    
    def get_periode_jour(self, obj):
        """Catégorise l'heure dans une période de la journée."""
        if 5 <= obj.heure < 12:
            return 'matin'
        elif 12 <= obj.heure < 14:
            return 'midi'
        elif 14 <= obj.heure < 18:
            return 'après-midi'
        elif 18 <= obj.heure < 22:
            return 'soirée'
        else:
            return 'nuit'
    
    def validate(self, data):
        """Validation croisée."""
        if 'date' in data and data['date'] > timezone.now().date():
            raise serializers.ValidationError({
                'date': 'La date ne peut pas être dans le futur'
            })
        
        return data


class AppareilSerializer(serializers.ModelSerializer):
    """Serializer pour les types d'appareils."""
    
    type_appareil = serializers.CharField(
        max_length=50,
        help_text="Type d'appareil (mobile, desktop, tablet)"
    )
    
    systeme_exploitation = serializers.CharField(
        max_length=100,
        help_text="Système d'exploitation"
    )
    
    visites = serializers.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Nombre de visites avec cet appareil"
    )
    
    # Champs calculés
    pourcentage_total = serializers.SerializerMethodField(read_only=True)
    icone_appareil = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Appareil
        fields = [
            'id', 'date', 'type_appareil', 'systeme_exploitation',
            'visites', 'pourcentage_total', 'icone_appareil',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_pourcentage_total(self, obj):
        """Calcule le pourcentage d'utilisation de cet appareil."""
        try:
            total_appareils_jour = Appareil.objects.filter(
                date=obj.date
            ).aggregate(total=Sum('visites'))['total'] or 0
            
            if total_appareils_jour > 0:
                return round((obj.visites / total_appareils_jour) * 100, 2)
        except:
            pass
        return 0.0
    
    def get_icone_appareil(self, obj):
        """Retourne une icône selon le type d'appareil."""
        icones = {
            'mobile': '📱',
            'desktop': '💻',
            'tablet': '📱',
            'tv': '📺',
            'bot': '🤖'
        }
        return icones.get(obj.type_appareil.lower(), '📱')


class NavigateurSerializer(serializers.ModelSerializer):
    """Serializer pour les navigateurs."""
    
    nom = serializers.CharField(
        max_length=100,
        help_text="Nom du navigateur"
    )
    
    version = serializers.CharField(
        max_length=50,
        help_text="Version du navigateur"
    )
    
    visites = serializers.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Nombre de visites avec ce navigateur"
    )
    
    # Champs calculés
    pourcentage_total = serializers.SerializerMethodField(read_only=True)
    icone_navigateur = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Navigateur
        fields = [
            'id', 'date', 'nom', 'version', 'visites',
            'pourcentage_total', 'icone_navigateur',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_pourcentage_total(self, obj):
        """Calcule le pourcentage d'utilisation de ce navigateur."""
        try:
            total_navigateurs_jour = Navigateur.objects.filter(
                date=obj.date
            ).aggregate(total=Sum('visites'))['total'] or 0
            
            if total_navigateurs_jour > 0:
                return round((obj.visites / total_navigateurs_jour) * 100, 2)
        except:
            pass
        return 0.0
    
    def get_icone_navigateur(self, obj):
        """Retourne une icône selon le navigateur."""
        navigateur = obj.nom.lower()
        if 'chrome' in navigateur:
            return '🌐'
        elif 'firefox' in navigateur:
            return '🦊'
        elif 'safari' in navigateur:
            return '🍎'
        elif 'edge' in navigateur:
            return '🔷'
        elif 'opera' in navigateur:
            return '🎭'
        else:
            return '🌐'


class DashboardSerializer(serializers.Serializer):
    """Serializer pour les données du tableau de bord."""
    
    periode = serializers.DictField(
        child=serializers.DateField(),
        help_text="Période analysée"
    )
    
    metriques = serializers.DictField(
        child=serializers.FloatField(),
        help_text="Métriques principales"
    )
    
    top_pages = serializers.ListField(
        child=serializers.DictField(),
        help_text="Top des pages les plus visitées"
    )
    
    top_pays = serializers.ListField(
        child=serializers.DictField(),
        help_text="Top des pays"
    )
    
    derniere_mise_a_jour = serializers.DateTimeField(
        help_text="Date de la dernière mise à jour"
    )


class TendancesSerializer(serializers.Serializer):
    """Serializer pour les données de tendances."""
    
    periode = serializers.CharField(
        help_text="Période analysée"
    )
    
    jours = serializers.IntegerField(
        help_text="Nombre de jours analysés"
    )
    
    metrique = serializers.CharField(
        help_text="Métrique analysée"
    )
    
    labels = serializers.ListField(
        child=serializers.CharField(),
        help_text="Labels pour l'axe X"
    )
    
    data = serializers.ListField(
        child=serializers.FloatField(),
        help_text="Données pour l'axe Y"
    )
    
    evolution = serializers.FloatField(
        help_text="Évolution en pourcentage"
    )
    
    moyenne = serializers.FloatField(
        help_text="Moyenne sur la période"
    )
    
    maximum = serializers.FloatField(
        help_text="Valeur maximale"
    )
    
    minimum = serializers.FloatField(
        help_text="Valeur minimale"
    )


class RapportSerializer(serializers.Serializer):
    """Serializer pour la génération de rapports."""
    
    date_debut = serializers.DateField(
        required=True,
        help_text="Date de début du rapport"
    )
    
    date_fin = serializers.DateField(
        required=True,
        help_text="Date de fin du rapport"
    )
    
    format = serializers.ChoiceField(
        choices=['pdf', 'excel', 'csv', 'html'],
        default='pdf',
        help_text="Format du rapport"
    )
    
    type_rapport = serializers.ChoiceField(
        choices=['complet', 'synthese', 'journalier', 'mensuel'],
        default='complet',
        help_text="Type de rapport"
    )
    
    inclure_graphiques = serializers.BooleanField(
        default=True,
        help_text="Inclure les graphiques dans le rapport"
    )
    
    email = serializers.EmailField(
        required=False,
        help_text="Email pour envoyer le rapport"
    )
    
    def validate(self, data):
        """Validation croisée des dates."""
        date_debut = data.get('date_debut')
        date_fin = data.get('date_fin')
        
        if date_debut and date_fin:
            if date_debut > date_fin:
                raise serializers.ValidationError({
                    'date_debut': 'La date de début doit être antérieure à la date de fin'
                })
            
            # Limiter à 365 jours maximum
            if (date_fin - date_debut).days > 365:
                raise serializers.ValidationError({
                    'date_fin': 'La période ne peut pas dépasser 365 jours'
                })
            
            # Ne pas permettre de dates dans le futur
            aujourdhui = timezone.now().date()
            if date_fin > aujourdhui:
                raise serializers.ValidationError({
                    'date_fin': 'La date de fin ne peut pas être dans le futur'
                })
        
        return data


class ExportSerializer(serializers.Serializer):
    """Serializer pour l'export de données."""
    
    date_debut = serializers.DateField(
        required=True,
        help_text="Date de début de l'export"
    )
    
    date_fin = serializers.DateField(
        required=True,
        help_text="Date de fin de l'export"
    )
    
    format = serializers.ChoiceField(
        choices=['csv', 'excel', 'json'],
        default='csv',
        help_text="Format d'export"
    )
    
    modeles = serializers.MultipleChoiceField(
        choices=[
            ('statsvisite', 'Visites'),
            ('pagevue', 'Pages vues'),
            ('referent', 'Référents'),
            ('paysvisite', 'Pays'),
            ('periodeactive', 'Périodes actives')
        ],
        default=['statsvisite'],
        help_text="Modèles à exporter"
    )
    
    compression = serializers.BooleanField(
        default=False,
        help_text="Compresser le fichier en ZIP"
    )
    
    def validate(self, data):
        """Validation croisée."""
        date_debut = data.get('date_debut')
        date_fin = data.get('date_fin')
        
        if date_debut and date_fin and date_debut > date_fin:
            raise serializers.ValidationError({
                'date_debut': 'La date de début doit être antérieure à la date de fin'
            })
        
        return data


class AlerteSerializer(serializers.Serializer):
    """Serializer pour les alertes."""
    
    type = serializers.CharField(
        help_text="Type d'alerte"
    )
    
    severite = serializers.ChoiceField(
        choices=['basse', 'moyenne', 'haute', 'critique'],
        help_text="Sévérité de l'alerte"
    )
    
    message = serializers.CharField(
        help_text="Message d'alerte"
    )
    
    date = serializers.DateField(
        help_text="Date de l'alerte"
    )
    
    details = serializers.DictField(
        help_text="Détails de l'alerte"
    )


class StatistiquesAggregeesSerializer(serializers.Serializer):
    """Serializer pour les statistiques agrégées."""
    
    periode = serializers.CharField(
        help_text="Période analysée"
    )
    
    total_visites = serializers.IntegerField(
        help_text="Total des visites"
    )
    
    total_pages_vues = serializers.IntegerField(
        help_text="Total des pages vues"
    )
    
    visites_moyennes = serializers.FloatField(
        help_text="Visites moyennes par jour"
    )
    
    pages_par_visite = serializers.FloatField(
        help_text="Pages par visite moyenne"
    )
    
    duree_moyenne = serializers.FloatField(
        help_text="Durée moyenne des visites"
    )
    
    taux_rebond_moyen = serializers.FloatField(
        help_text="Taux de rebond moyen"
    )
    
    meilleur_jour = serializers.DictField(
        help_text="Meilleur jour de la période"
    )
    
    repartition_weekend = serializers.DictField(
        help_text="Répartition weekend/semaine"
    )


class ImportStatsSerializer(serializers.Serializer):
    """Serializer pour l'import de statistiques."""
    
    fichier = serializers.FileField(
        help_text="Fichier à importer (CSV, Excel, JSON)"
    )
    
    source = serializers.ChoiceField(
        choices=['google_analytics', 'matomo', 'fichier', 'api'],
        default='fichier',
        help_text="Source des données"
    )
    
    date_debut = serializers.DateField(
        required=False,
        help_text="Date de début (si applicable)"
    )
    
    date_fin = serializers.DateField(
        required=False,
        help_text="Date de fin (si applicable)"
    )
    
    ecraser = serializers.BooleanField(
        default=False,
        help_text="Écraser les données existantes"
    )
    
    def validate_fichier(self, value):
        """Valide le fichier d'import."""
        # Vérifier la taille (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Le fichier est trop volumineux. Taille max: {max_size / (1024*1024)}MB"
            )
        
        # Vérifier l'extension
        extensions_valides = ['.csv', '.xlsx', '.xls', '.json']
        filename = value.name.lower()
        
        if not any(filename.endswith(ext) for ext in extensions_valides):
            raise serializers.ValidationError(
                f"Format de fichier non supporté. Formats valides: {', '.join(extensions_valides)}"
            )
        
        return value