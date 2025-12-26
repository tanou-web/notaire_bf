from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP
from .models import PaiementsTransaction
from apps.demandes.models import DemandesDemande


class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaiementsTransaction
        fields = '__all__'


class PaiementCreateSerializer(serializers.Serializer):
    demande_id = serializers.IntegerField()
    type_paiement = serializers.ChoiceField(choices=[c[0] for c in PaiementsTransaction.TYPE_CHOICES])

    def validate_demande_id(self, value):
        try:
            DemandesDemande.objects.get(id=value)
        except DemandesDemande.DoesNotExist:
            raise serializers.ValidationError('Demande introuvable')
        return value

    def create(self, validated_data):
        demande = DemandesDemande.objects.get(id=validated_data['demande_id'])

        # Montant de la demande
        from rest_framework import serializers
        from decimal import Decimal, ROUND_HALF_UP
        import uuid
        from datetime import datetime
        from django.utils import timezone
        from django.core.exceptions import ValidationError
        from .models import PaiementsTransaction
        from apps.demandes.models import DemandesDemande


        class PaiementSerializer(serializers.ModelSerializer):
            """Serializer pour la lecture des paiements"""
            type_paiement_display = serializers.SerializerMethodField()
            statut_display = serializers.SerializerMethodField()
            montant_formate = serializers.SerializerMethodField()
            commission_formate = serializers.SerializerMethodField()
            montant_total_formate = serializers.SerializerMethodField()
            demande_reference = serializers.CharField(source='demande.reference', read_only=True)
            utilisateur_email = serializers.CharField(source='demande.utilisateur.email', read_only=True)
            delai_validation = serializers.SerializerMethodField()
    
            class Meta:
                model = PaiementsTransaction
                fields = [
                    'id', 'reference', 'demande', 'demande_reference', 'utilisateur_email',
                    'type_paiement', 'type_paiement_display', 'montant', 'montant_formate',
                    'commission', 'commission_formate', 'montant_total_formate',
                    'statut', 'statut_display', 'donnees_api',
                    'date_creation', 'date_maj', 'date_validation', 'delai_validation'
                ]
                read_only_fields = [
                    'reference', 'montant', 'commission', 'donnees_api',
                    'date_creation', 'date_maj', 'date_validation'
                ]
    
            def get_type_paiement_display(self, obj):
                """Afficher le type de paiement en français"""
                return {
                    'orange_money': 'Orange Money',
                    'moov_money': 'Moov Money'
                }.get(obj.type_paiement, obj.type_paiement)
    
            def get_statut_display(self, obj):
                """Afficher le statut en français"""
                return {
                    'initie': 'Initié',
                    'en_attente': 'En attente',
                    'reussi': 'Réussi',
                    'echec': 'Échec'
                }.get(obj.statut, obj.statut)
    
            def get_montant_formate(self, obj):
                """Formater le montant"""
                return f"{obj.montant:,.0f} FCFA".replace(",", " ")
    
            def get_commission_formate(self, obj):
                """Formater la commission"""
                return f"{obj.commission:,.0f} FCFA".replace(",", " ")
    
            def get_montant_total_formate(self, obj):
                """Formater le montant total (montant + commission)"""
                total = obj.montant + obj.commission
                return f"{total:,.0f} FCFA".replace(",", " ")
    
            def get_delai_validation(self, obj):
                """Calculer le délai de validation"""
                if obj.date_validation and obj.date_creation:
                    delta = obj.date_validation - obj.date_creation
                    seconds = delta.total_seconds()
            
                    if seconds < 60:
                        return f"{int(seconds)} secondes"
                    elif seconds < 3600:
                        return f"{int(seconds/60)} minutes"
                    else:
                        return f"{int(seconds/3600)} heures {int((seconds % 3600)/60)} minutes"
                return None


        class PaiementCreateSerializer(serializers.Serializer):
            """Serializer pour créer un paiement"""
            demande_id = serializers.IntegerField()
            type_paiement = serializers.ChoiceField(choices=['orange_money', 'moov_money'])
    
            def validate_demande_id(self, value):
                """Valider que la demande existe et est éligible au paiement"""
                try:
                    demande = DemandesDemande.objects.get(id=value)
            
                    # Vérifier que la demande est en attente de paiement
                    if demande.statut != 'attente_paiement':
                        raise serializers.ValidationError(
                            f"La demande doit être en statut 'attente_paiement'. Statut actuel: {demande.statut}"
                        )
            
                    # Vérifier qu'il n'y a pas déjà un paiement pour cette demande
                    if hasattr(demande, 'paiementstransaction'):
                        raise serializers.ValidationError('Un paiement existe déjà pour cette demande')
            
                    return value
                except DemandesDemande.DoesNotExist:
                    raise serializers.ValidationError('Demande introuvable')
    
            def validate(self, data):
                """Validation globale"""
                demande_id = data['demande_id']
                demande = DemandesDemande.objects.get(id=demande_id)
        
                # Vérifier que l'utilisateur est le propriétaire de la demande
                request = self.context.get('request')
                if request and request.user != demande.utilisateur:
                    raise serializers.ValidationError("Vous n'êtes pas autorisé à payer cette demande")
        
                return data
    
            def create(self, validated_data):
                """Créer la transaction de paiement"""
                demande = DemandesDemande.objects.get(id=validated_data['demande_id'])
                type_paiement = validated_data['type_paiement']
        
                # Montant de la demande
                montant = demande.montant_total
        
                # Calculer commission 3%
                commission = (Decimal(montant) * Decimal('0.03')).quantize(
                    Decimal('0.01'), 
                    rounding=ROUND_HALF_UP
                )
        
                # Générer une référence unique avec timestamp
                timestamp = int(timezone.now().timestamp() * 1000)  # Millisecondes
                unique_id = str(uuid.uuid4().hex[:8].upper())
                reference = f"TXN-{timestamp}-{unique_id}"
        
                # Créer la transaction
                transaction = PaiementsTransaction.objects.create(
                    reference=reference,
                    demande=demande,
                    type_paiement=type_paiement,
                    montant=montant,
                    commission=commission,
                    statut='initie',
                    donnees_api={
                        'initiated_at': timezone.now().isoformat(),
                        'provider': type_paiement,
                        'montant': float(montant),
                        'commission': float(commission),
                        'demande_reference': demande.reference
                    },
                    date_creation=timezone.now(),
                    date_maj=timezone.now()
                )
        
                # Mettre à jour le statut de la demande
                demande.statut = 'attente_paiement'
                demande.save()
        
                return transaction
    

        class PaiementUpdateSerializer(serializers.ModelSerializer):
            """Serializer pour mettre à jour un paiement (admin seulement)"""
            class Meta:
                model = PaiementsTransaction
                fields = ['statut', 'donnees_api']
        
            def update(self, instance, validated_data):
                """Mettre à jour avec gestion de la date de validation"""
                new_statut = validated_data.get('statut', instance.statut)
        
                # Si le statut passe à 'reussi', mettre à jour la date de validation
                if new_statut == 'reussi' and instance.statut != 'reussi':
                    validated_data['date_validation'] = timezone.now()
            
                    # Mettre à jour le statut de la demande
                    demande = instance.demande
                    demande.statut = 'en_attente_traitement'
                    demande.save()
        
                # Mettre à jour la date de modification
                validated_data['date_maj'] = timezone.now()
        
                return super().update(instance, validated_data)
    

        class WebhookSerializer(serializers.Serializer):
            """Serializer pour les webhooks des opérateurs de paiement"""
            reference = serializers.CharField(max_length=100)
            statut = serializers.ChoiceField(choices=[
                'success', 'failed', 'pending',  # Formats courants des opérateurs
                'SUCCESS', 'FAILED', 'PENDING',  # Autres formats possibles
                'COMPLETED', 'CANCELLED'
            ])
            montant = serializers.DecimalField(
                max_digits=10, 
                decimal_places=2, 
                required=False,
                help_text="Montant vérifié (optionnel)"
            )
            transaction_id = serializers.CharField(
                max_length=100, 
                required=False,
                help_text="ID de transaction de l'opérateur"
            )
            donnees = serializers.JSONField(
                required=False,
                help_text="Données supplémentaires du webhook"
            )
            signature = serializers.CharField(
                max_length=500, 
                required=False,
                help_text="Signature pour vérifier l'authenticité"
            )
            timestamp = serializers.CharField(
                max_length=50,
                required=False,
                help_text="Horodatage du webhook"
            )
    
            def validate(self, data):
                """Validation avancée du webhook"""
                reference = data.get('reference')
        
                # Normaliser le statut
                statut = data.get('statut', '').upper()
                statut_normalise = {
                    'SUCCESS': 'reussi',
                    'COMPLETED': 'reussi',
                    'FAILED': 'echec',
                    'CANCELLED': 'echec',
                    'PENDING': 'en_attente'
                }.get(statut, 'en_attente')
        
                data['statut_normalise'] = statut_normalise
        
                # Si un montant est fourni, le valider
                montant = data.get('montant')
                if montant:
                    try:
                        # Essayer de trouver la transaction
                        transaction = PaiementsTransaction.objects.get(reference=reference)
                
                        # Vérifier que le montant correspond (avec une marge d'erreur de 1%)
                        montant_attendu = float(transaction.montant)
                        montant_recu = float(montant)
                
                        if abs(montant_recu - montant_attendu) / montant_attendu > 0.01:
                            raise serializers.ValidationError({
                                'montant': f'Montant incorrect. Attendu: {montant_attendu}, Reçu: {montant_recu}'
                            })
            
                    except PaiementsTransaction.DoesNotExist:
                        pass  # On continue sans vérification
        
                return data
    
    
        class InitierPaiementResponseSerializer(serializers.Serializer):
            """Serializer pour la réponse d'initiation de paiement"""
            status = serializers.CharField(default='success')
            message = serializers.CharField()
            transaction = PaiementSerializer()
            payment_url = serializers.URLField(required=False)
            api_data = serializers.JSONField(required=False)
    
            class Meta:
                fields = ['status', 'message', 'transaction', 'payment_url', 'api_data']
    
    
        class StatistiquesPaiementSerializer(serializers.Serializer):
            """Serializer pour les statistiques de paiement"""
            total_transactions = serializers.IntegerField()
            transactions_reussies = serializers.IntegerField()
            transactions_en_attente = serializers.IntegerField()
            transactions_echec = serializers.IntegerField()
            montant_total = serializers.DecimalField(max_digits=15, decimal_places=2)
            commission_totale = serializers.DecimalField(max_digits=15, decimal_places=2)
            moyenne_montant = serializers.DecimalField(max_digits=10, decimal_places=2)
    
            class Meta:
                fields = [
                    'total_transactions', 'transactions_reussies', 
                    'transactions_en_attente', 'transactions_echec',
                    'montant_total', 'commission_totale', 'moyenne_montant'
                ]