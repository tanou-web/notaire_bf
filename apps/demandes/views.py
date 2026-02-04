from rest_framework import viewsets, filters, status, permissions
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from .models import DemandesDemande, DemandesPieceJointe
from .serializers import (
    DemandeSerializer, DemandeCreateSerializer,
    PieceJointeSerializer, PieceJointeCreateSerializer
)
from apps.utilisateurs.permissions import IsOwnerOrReadOnly

class DemandeViewSet(viewsets.ModelViewSet):
    queryset = DemandesDemande.objects.all()
    serializer_class = DemandeSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['statut', 'document', 'notaire']
    search_fields = ['reference', 'email_reception']
    ordering_fields = ['created_at', 'updated_at', 'montant_total']
    
    def get_queryset(self):
        """
        Filtre les demandes selon l'utilisateur :
        - Admin/Superuser : voit toutes les demandes
        - Utilisateur authentifié : voit ses propres demandes
        - Utilisateur anonyme : peut filtrer par email ou référence via query params
        """
        user = self.request.user
        if user.is_superuser or user.is_staff:
            queryset = DemandesDemande.objects.all()
        elif user.is_authenticated:
            queryset = DemandesDemande.objects.filter(utilisateur=user)
        else:
            # Utilisateur anonyme : peut voir une demande spécifique par email ou référence
            email = self.request.query_params.get('email')
            reference = self.request.query_params.get('reference')

            queryset = DemandesDemande.objects.none()
            if email:
                queryset = DemandesDemande.objects.filter(email_reception=email)
            elif reference:
                queryset = DemandesDemande.objects.filter(reference=reference)
            else:
                queryset = DemandesDemande.objects.none()

        # Support du paramètre 'q' pour la recherche générale
        search_query = self.request.query_params.get('q', None)
        if search_query:
            queryset = queryset.filter(
                Q(reference__icontains=search_query) |
                Q(email_reception__icontains=search_query) |
                Q(prenom_reception__icontains=search_query) |
                Q(nom_reception__icontains=search_query)
            )

        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DemandeCreateSerializer
        return super().get_serializer_class()
    
    def create(self, request, *args, **kwargs):
        """
        Création d'une demande.
        Supporte le parsing JSON manuel pour donnees_formulaire si envoyé via multipart/form-data.
        """
        import json
        # Utiliser un dictionnaire simple pour les données modifiables
        mutable_data = request.data.dict()
        
        # Gérer donnees_formulaire si c'est une chaîne JSON (cas du multipart/form-data)
        donnees_formulaire = mutable_data.get('donnees_formulaire')
        if isinstance(donnees_formulaire, str) and donnees_formulaire:
            try:
                # On remplace la chaîne par l'objet Python parsé
                mutable_data['donnees_formulaire'] = json.loads(donnees_formulaire)
            except json.JSONDecodeError:
                pass

        # Utiliser les données préparées
        serializer = self.get_serializer(data=mutable_data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer la demande
        demande = serializer.save()
        
        # Traiter les fichiers envoyés comme pièces jointes (Optionnel / Automatique)
        if request.FILES:
            for key, file_obj in request.FILES.items():
                try:
                    # Déterminer le type de pièce
                    type_piece = 'autre'
                    known_types = [choice[0] for choice in DemandesPieceJointe.TYPE_PIECE_CHOICES]
                    if key in known_types:
                        type_piece = key
                    elif 'fichier_champ_' in key:
                        type_piece = 'document_legal'
                    
                    DemandesPieceJointe.objects.create(
                        demande=demande,
                        type_piece=type_piece,
                        fichier=file_obj,
                        nom_original=file_obj.name,
                        taille_fichier=file_obj.size
                    )
                except Exception as e:
                    # On log l'erreur S3 mais on ne fait pas échouer la création de la demande
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Erreur S3 lors de l'upload auto de {key}: {str(e)}")

        # Retourner la réponse complète avec tous les détails
        full_serializer = DemandeSerializer(demande, context=self.get_serializer_context())
        return Response(full_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def assigner_notaire(self, request, pk=None):
        demande = self.get_object()
        notaire_id = request.data.get('notaire_id')
        
        # Logique d'assignation
        from apps.notaires.models import NotairesNotaire
        try:
            notaire = NotairesNotaire.objects.get(id=notaire_id, actif=True)
            demande.notaire = notaire
            demande.date_attribution = timezone.now()
            demande.statut = 'en_traitement'
            demande.save()
            
            return Response({
                'status': 'success',
                'message': f'Notaire {notaire.nom} assigné à la demande',
                'demande': DemandeSerializer(demande).data
            })
        except NotairesNotaire.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Notaire non trouvé ou inactif'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def completer_traitement(self, request, pk=None):
        """Compléter le traitement d'une demande et envoyer le document par email"""
        demande = self.get_object()
        document_genere = request.FILES.get('document_genere')

        if not document_genere:
            return Response({
                'error': 'Le document généré est requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier que l'email de réception est fourni
        if not demande.email_reception:
            return Response({
                'error': 'Aucun email de réception spécifié pour cette demande'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Sauvegarder le document généré
        # Le document_genere est un CharField qui stocke le chemin/nom du fichier
        document_genere.name  # S'assurer que le fichier a un nom
        
        # Envoyer l'email avec le document en pièce jointe
        try:
            from django.core.mail import EmailMessage
            from django.conf import settings
            
            # Lire le contenu du fichier avant de l'envoyer
            document_genere.seek(0)  # Se repositionner au début du fichier
            document_content = document_genere.read()
            document_genere.seek(0)  # Se repositionner à nouveau pour sauvegarde
            
            sujet = f"Votre document - Demande {demande.reference}"
            message = f"""
Bonjour,

Votre demande de document (Référence: {demande.reference}) a été traitée avec succès.

Détails de la commande :
- Référence : {demande.reference}
- Document : {demande.document.titre if hasattr(demande.document, 'titre') else 'Document'}
- Montant payé : {demande.montant_total} FCFA

Le document demandé est joint à cet email.

Cordialement,
L'Ordre des Notaires du Burkina Faso
"""
            
            email = EmailMessage(
                sujet,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [demande.email_reception],
            )
            
            # Attacher le document généré
            email.attach(
                document_genere.name,
                document_content,
                document_genere.content_type
            )
            
            email.send()
            
            # Sauvegarder le nom du fichier dans le modèle
            demande.document_genere = document_genere.name
            demande.statut = 'document_envoye_email'
            demande.date_envoi_email = timezone.now()
            demande.save()
            
            return Response({
                'status': 'success',
                'message': f'Document envoyé par email à {demande.email_reception}',
                'demande': DemandeSerializer(demande, context={'request': request}).data
            })
            
        except Exception as e:
            # En cas d'erreur d'envoi, retourner une erreur
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de l'envoi de l'email pour la demande {demande.id}: {str(e)}")
            
            return Response({
                'status': 'error',
                'message': f'Erreur lors de l\'envoi de l\'email : {str(e)}',
                'demande': DemandeSerializer(demande, context={'request': request}).data
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PieceJointeViewSet(viewsets.ModelViewSet):
    """API pour les pièces jointes des demandes"""
    queryset = DemandesPieceJointe.objects.all()
    serializer_class = PieceJointeSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['demande', 'type_piece']
    ordering_fields = ['created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PieceJointeCreateSerializer
        return PieceJointeSerializer

    def get_permissions(self):
        if self.action == 'create':
            return []  # autorise tout le monde pour créer
        return [permission() for permission in self.permission_classes]

    
    def get_queryset(self):
        user = self.request.user
        # Les utilisateurs voient seulement les pièces jointes de leurs demandes
        if user.is_superuser or user.is_staff:
            return DemandesPieceJointe.objects.all()
        return DemandesPieceJointe.objects.filter(demande__utilisateur=user)

    
    def perform_create(self, serializer):
        demande_id = serializer.validated_data.get('demande')
        if not demande_id:
            raise serializers.ValidationError({'demande': 'La demande est requise'})
        
        try:
            demande = DemandesDemande.objects.get(id=demande_id.id if hasattr(demande_id, 'id') else demande_id)
        except DemandesDemande.DoesNotExist:
            raise serializers.ValidationError({'demande': 'Demande introuvable'})
        
        # Vérifier que l'utilisateur peut ajouter des pièces à cette demande
        if not self.request.user.is_staff and demande.utilisateur not in [self.request.user, None]:
            raise permissions.PermissionDenied("Vous ne pouvez pas ajouter de pièce jointe à cette demande")
        serializer.save()