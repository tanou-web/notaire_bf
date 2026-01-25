import json
from rest_framework import serializers
from django.db import transaction
 
from .models import (
    Evenement,
    EvenementChamp,
    Inscription,
    InscriptionReponse
)

# =========================
# EVENEMENT / CHAMPS
# =========================

class EvenementChampCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)  # 🔴 IMPORTANT pour update

    class Meta:
        model = EvenementChamp
        fields = ['id', 'label', 'type', 'obligatoire', 'ordre', 'options', 'actif']


class EvenementSerializer(serializers.ModelSerializer):
    champs = EvenementChampCreateSerializer(many=True)

    class Meta:
        model = Evenement
        fields = [
            'id',
            'titre',
            'description',
            'statut',
            'actif',
            'nombre_places',
            'created_at',
            'champs'
        ]

    def create(self, validated_data):
        champs_data = validated_data.pop('champs', [])
        evenement = Evenement.objects.create(**validated_data)

        for champ_data in champs_data:
            EvenementChamp.objects.create(
                evenement=evenement,
                **champ_data
            )

        return evenement

    from django.db import transaction

    def update(self, instance, validated_data):
        champs_data = validated_data.pop('champs', [])

        with transaction.atomic():

            # 1️⃣ Update des champs simples de l’événement
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # 2️⃣ Champs existants en base
            champs_existants = {
                champ.id: champ
                for champ in instance.champs.all()
            }

            ids_conserves = []

            # 3️⃣ CREATE / UPDATE
            for champ_data in champs_data:
                champ_id = champ_data.pop('id', None)

                # 🟢 UPDATE (id réel en base)
                if champ_id and champ_id in champs_existants:
                    champ = champs_existants[champ_id]
                    for key, value in champ_data.items():
                        setattr(champ, key, value)
                    champ.save()
                    ids_conserves.append(champ_id)

                # 🟢 CREATE (nouveau champ)
                else:
                    nouveau = EvenementChamp.objects.create(
                        evenement=instance,
                        **champ_data
                    )
                    ids_conserves.append(nouveau.id)

            # 4️⃣ DELETE (champs supprimés côté frontend)
            instance.champs.exclude(id__in=ids_conserves).delete()

        return instance



# =========================
# INSCRIPTION (PUBLIC)
# =========================

class ReponseChampSerializer(serializers.Serializer):
    """Serializer pour une réponse individuelle à un champ"""
    champ = serializers.IntegerField()
    valeur = serializers.CharField()  # On accepte tout comme string, on caste après


class ReponsesJSONField(serializers.Field):
    """Champ personnalisé qui parse automatiquement le JSON stringifié"""

    def to_internal_value(self, data):
        if isinstance(data, str):
            import json
            try:
                parsed_data = json.loads(data)
                # Valider chaque élément avec ReponseChampSerializer
                serializer = ReponseChampSerializer(data=parsed_data, many=True)
                if serializer.is_valid():
                    return serializer.validated_data
                else:
                    raise serializers.ValidationError(serializer.errors)
            except (ValueError, TypeError):
                raise serializers.ValidationError('Format JSON invalide pour les réponses.')
        elif isinstance(data, list):
            # Si c'est déjà une liste (cas rare), la valider directement
            serializer = ReponseChampSerializer(data=data, many=True)
            if serializer.is_valid():
                return serializer.validated_data
            else:
                raise serializers.ValidationError(serializer.errors)
        else:
            raise serializers.ValidationError('Les réponses doivent être une liste ou une chaîne JSON.')


class InscriptionCreateSerializer(serializers.Serializer):
    evenement = serializers.PrimaryKeyRelatedField(
        queryset=Evenement.objects.all()
    )
    nom = serializers.CharField()
    prenom = serializers.CharField()
    email = serializers.EmailField()
    telephone = serializers.CharField()

    reponses = ReponsesJSONField(write_only=True)

    # La méthode to_internal_value n'est plus nécessaire car ReponsesJSONField gère le parsing


    def validate(self, data):
        evenement = data['evenement']
        reponses = data['reponses']

        champs = EvenementChamp.objects.filter(
            evenement=evenement,
            actif=True
        )

        champs_map = {c.id: c for c in champs}
        champs_obligatoires = {c.id for c in champs if c.obligatoire}
        champs_envoyes = {r.get('champ') for r in reponses}

        manquants = champs_obligatoires - champs_envoyes
        if manquants:
            raise serializers.ValidationError(
                "Certains champs obligatoires sont manquants"
            )

        for r in reponses:
            champ_id = r.get('champ')
            valeur = r.get('valeur')

            if champ_id not in champs_map:
                raise serializers.ValidationError("Champ invalide")

            champ = champs_map[champ_id]

            # Validation des champs obligatoires
            if champ.obligatoire:
                if champ.type == 'file':
                    # Pour les fichiers, vérifier que request.FILES contient le fichier
                    request = self.context.get('request')
                    if request and hasattr(request, 'FILES'):
                        file_key = f'fichier_champ_{champ_id}'
                        if file_key not in request.FILES or request.FILES[file_key].size == 0:
                            raise serializers.ValidationError(
                                f"{champ.label} est obligatoire (fichier requis)"
                            )
                    else:
                        raise serializers.ValidationError(
                            f"{champ.label} est obligatoire (fichier requis)"
                        )
                elif valeur in [None, '', []]:
                    raise serializers.ValidationError(
                        f"{champ.label} est obligatoire"
                    )

            if champ.type == 'number' and not isinstance(valeur, (int, float)):
                raise serializers.ValidationError(
                    f"{champ.label} doit être un nombre"
                )

            if champ.type == 'select':
                if not champ.options or valeur not in champ.options:
                    raise serializers.ValidationError(
                        f"Valeur invalide pour {champ.label}"
                    )

            if champ.type == 'checkbox' and not isinstance(valeur, bool):
                raise serializers.ValidationError(
                    f"{champ.label} doit être vrai ou faux"
                )

            if champ.type == 'date' and valeur:
                from datetime import datetime
                try:
                    # Essayer d'abord le format ISO (AAAA-MM-JJ)
                    datetime.strptime(str(valeur), '%Y-%m-%d')
                except ValueError:
                    try:
                        # Essayer le format français (JJ/MM/AAAA)
                        datetime.strptime(str(valeur), '%d/%m/%Y')
                    except ValueError:
                        raise serializers.ValidationError(
                            f"Format de date invalide pour {champ.label}. Utilisez AAAA-MM-JJ ou JJ/MM/AAAA"
                        )

            if champ.type == 'file':
                # Validation du fichier depuis request.FILES
                request = self.context.get('request')
                if request and hasattr(request, 'FILES'):
                    file_key = f'fichier_champ_{champ_id}'
                    if file_key in request.FILES:
                        fichier = request.FILES[file_key]
                        # Validation basique du fichier
                        if fichier.size > 10 * 1024 * 1024:  # 10MB max
                            raise serializers.ValidationError(
                                f"Fichier trop volumineux pour {champ.label} (max 10MB)"
                            )
                        # Vérifier l'extension si nécessaire
                        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
                        import os
                        ext = os.path.splitext(fichier.name)[1].lower()
                        if ext not in allowed_extensions:
                            raise serializers.ValidationError(
                                f"Type de fichier non autorisé pour {champ.label}. Extensions acceptées: {', '.join(allowed_extensions)}"
                            )

        # Vérifier si l'événement a des places restantes
        if evenement.nombre_places <= 0:
            raise serializers.ValidationError("Toutes les places pour cet événement sont déjà réservées.")

        return data

    def create(self, validated_data):
        reponses_data = validated_data.pop('reponses')
        evenement = validated_data['evenement']

        # Créer l'inscription
        inscription = Inscription.objects.create(**validated_data)

        # Créer les réponses aux champs
        request = self.context.get('request')
        for r in reponses_data:
            champ = EvenementChamp.objects.get(id=r['champ'])
            valeur = r.get('valeur')
            reponse = InscriptionReponse(inscription=inscription, champ=champ)
            if champ.type in ['text', 'textarea', 'select']:
                reponse.valeur_texte = valeur
            elif champ.type == 'number':
                reponse.valeur_nombre = valeur
            elif champ.type == 'date':
                from datetime import datetime
                # Convertir la date du format français JJ/MM/AAAA vers AAAA-MM-JJ
                if isinstance(valeur, str) and valeur:
                    try:
                        # Essayer d'abord le format ISO (AAAA-MM-JJ)
                        reponse.valeur_date = datetime.strptime(valeur, '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            # Essayer le format français (JJ/MM/AAAA)
                            reponse.valeur_date = datetime.strptime(valeur, '%d/%m/%Y').date()
                        except ValueError:
                            raise serializers.ValidationError(f"Format de date invalide pour {champ.label}. Utilisez AAAA-MM-JJ ou JJ/MM/AAAA")
                else:
                    reponse.valeur_date = valeur
            elif champ.type == 'checkbox':
                reponse.valeur_bool = valeur
            elif champ.type == 'file':
                # Pour les fichiers, récupérer depuis request.FILES avec la clé fichier_champ_{id}
                if request and hasattr(request, 'FILES'):
                    file_key = f'fichier_champ_{champ.id}'
                    if file_key in request.FILES:
                        reponse.valeur_fichier = request.FILES[file_key]
                    else:
                        # Si pas de fichier trouvé, utiliser None (champ optionnel)
                        reponse.valeur_fichier = None
                else:
                    reponse.valeur_fichier = None
            reponse.save()

        # Décrémenter le nombre de places
        evenement.nombre_places -= 1
        if evenement.nombre_places <= 0:
            evenement.statut = 'complet'  # mettre à jour le statut
        evenement.save()

        # Retourner l'inscription avec les réponses (format manuel pour éviter les erreurs de sérialisation)
        reponses_data = []
        for r in inscription.reponses.all():
            # Déterminer la valeur en fonction du type de champ
            valeur = None
            if r.champ.type == 'text' or r.champ.type == 'textarea' or r.champ.type == 'select':
                valeur = r.valeur_texte
            elif r.champ.type == 'number':
                valeur = r.valeur_nombre
            elif r.champ.type == 'date':
                valeur = r.valeur_date.isoformat() if r.valeur_date else None
            elif r.champ.type == 'checkbox':
                valeur = r.valeur_bool
            elif r.champ.type == 'file':
                valeur = str(r.valeur_fichier) if r.valeur_fichier else None

            reponses_data.append({
                "champ": r.champ.label,
                "type": r.champ.type,
                "valeur": valeur
            })

        return {
            'id': inscription.id,
            'evenement': inscription.evenement.id,  # Retourner l'ID, pas l'objet
            'nom': inscription.nom,
            'prenom': inscription.prenom,
            'email': inscription.email,
            'telephone': inscription.telephone,
            'statut': inscription.statut,
            'created_at': inscription.created_at,
            'reponses': reponses_data
        }


# =========================
# INSCRIPTION (ADMIN)
# =========================

class InscriptionSerializer(serializers.ModelSerializer):
    reponses = serializers.SerializerMethodField()

    class Meta:
        model = Inscription
        fields = [
            'id',
            'evenement',
            'nom',
            'prenom',
            'email',
            'telephone',
            'statut',
            'created_at',
            'reponses'
        ]

    def get_reponses(self, obj):
        reponses = []
        for r in obj.reponses.all():
            # Déterminer la valeur en fonction du type de champ
            valeur = None
            if r.champ.type == 'text' or r.champ.type == 'textarea' or r.champ.type == 'select':
                valeur = r.valeur_texte
            elif r.champ.type == 'number':
                valeur = r.valeur_nombre
            elif r.champ.type == 'date':
                valeur = r.valeur_date
            elif r.champ.type == 'checkbox':
                valeur = r.valeur_bool
            elif r.champ.type == 'file':
                valeur = str(r.valeur_fichier) if r.valeur_fichier else None

            reponses.append({
                "champ": r.champ.label,
                "type": r.champ.type,
                "valeur": valeur
            })

        return reponses

