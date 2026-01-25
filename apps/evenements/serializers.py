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
    valeur = serializers.JSONField(required=False, allow_null=True)


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

    # =========================
    # FILE HELPERS
    # =========================

    def _get_file(self, champ_id):
        request = self.context.get('request')
        if not request:
            return None
        return request.FILES.get(f'fichier_champ_{champ_id}')

    def _validate_file(self, champ, fichier):
        if not fichier:
            if champ.obligatoire:
                raise serializers.ValidationError(
                    f"{champ.label} est obligatoire"
                )
            return

        if fichier.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                f"{champ.label} : fichier trop volumineux (max 10MB)"
            )

        import os
        ext = os.path.splitext(fichier.name)[1].lower()
        allowed = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
        if ext not in allowed:
            raise serializers.ValidationError(
                f"{champ.label} : type de fichier non autorisé"
            )

    # =========================
    # VALIDATION
    # =========================

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
            champ_id = r['champ']
            valeur = r.get('valeur')

            if champ_id not in champs_map:
                raise serializers.ValidationError("Champ invalide")

            champ = champs_map[champ_id]

            if champ.type == 'file':
                fichier = self._get_file(champ_id)
                self._validate_file(champ, fichier)
                continue

            if champ.type in ['text', 'textarea', 'select']:
                if (valeur in [None, ""]) and champ.obligatoire:
                    raise serializers.ValidationError(
                        f"{champ.label} est obligatoire"
                    )

            if champ.type == 'number':
                if valeur in [None, ""]:
                    if champ.obligatoire:
                        raise serializers.ValidationError(
                            f"{champ.label} est obligatoire"
                        )
                else:
                    try:
                        r['valeur'] = int(valeur)  # ✅ persistance
                    except (TypeError, ValueError):
                        raise serializers.ValidationError(
                            f"{champ.label} doit être un nombre valide"
                        )

            if champ.type == 'checkbox':
                if not isinstance(valeur, bool) and champ.obligatoire:
                    raise serializers.ValidationError(
                        f"{champ.label} doit être vrai ou faux"
                    )

        if evenement.nombre_places <= 0:
            raise serializers.ValidationError(
                "Toutes les places sont déjà réservées"
            )

        if champ.type == 'select':
            if champ.options:
                if valeur not in champ.options:
                    raise serializers.ValidationError(
                        f"Valeur invalide pour {champ.label}"
                    )


        return data

    # =========================
    # CREATE (OBLIGATOIRE)
    # =========================

    def create(self, validated_data):
        with transaction.atomic():
            evenement = validated_data['evenement']
            reponses = validated_data.pop('reponses')

            inscription = Inscription.objects.create(
                evenement=evenement,
                nom=validated_data['nom'],
                prenom=validated_data['prenom'],
                email=validated_data['email'],
                telephone=validated_data['telephone'],
            )

            champs_map = {
                c.id: c for c in EvenementChamp.objects.filter(
                    evenement=evenement,
                    actif=True
                )
            }

            for r in reponses:
                champ = champs_map[r['champ']]
                valeur = r.get('valeur')

                reponse = InscriptionReponse(
                    inscription=inscription,
                    champ=champ
                )

                if champ.type in ['text', 'textarea', 'select']:
                    reponse.valeur_texte = valeur
                elif champ.type == 'number':
                    reponse.valeur_nombre = valeur
                elif champ.type == 'date':
                    reponse.valeur_date = valeur
                elif champ.type == 'checkbox':
                    reponse.valeur_bool = valeur
                elif champ.type == 'file':
                    reponse.valeur_fichier = self._get_file(champ.id)

                reponse.save()

            evenement.nombre_places -= 1
            evenement.save(update_fields=['nombre_places'])

            return inscription


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
    def _get_file(self, champ_id):
        request = self.context.get('request')
        if not request:
            return None
        return request.FILES.get(f'fichier_champ_{champ_id}')

    def _validate_file(self, champ, fichier):
        if not fichier:
            if champ.obligatoire:
                raise serializers.ValidationError(
                    f"{champ.label} est obligatoire (fichier requis)"
                )
            return

        if fichier.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                f"Fichier trop volumineux pour {champ.label} (max 10MB)"
            )

        import os
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
        ext = os.path.splitext(fichier.name)[1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"Type de fichier non autorisé pour {champ.label}"
            )



