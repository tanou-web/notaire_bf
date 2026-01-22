from rest_framework import serializers
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

    def update(self, instance, validated_data):
        champs_data = validated_data.pop('champs', [])

        # 1️⃣ Update événement
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 2️⃣ IDs reçus du frontend
        incoming_ids = [
            champ.get('id')
            for champ in champs_data
            if champ.get('id')
        ]

        # 3️⃣ Supprimer les champs supprimés côté frontend
        EvenementChamp.objects.filter(
            evenement=instance
        ).exclude(id__in=incoming_ids).delete()

        # 4️⃣ Créer / mettre à jour les champs
        for champ_data in champs_data:
            champ_id = champ_data.pop('id', None)

            if champ_id:
                # UPDATE
                champ = EvenementChamp.objects.get(
                    id=champ_id,
                    evenement=instance
                )
                for key, value in champ_data.items():
                    setattr(champ, key, value)
                champ.save()
            else:
                # CREATE
                EvenementChamp.objects.create(
                    evenement=instance,
                    **champ_data
                )

        return instance


# =========================
# INSCRIPTION (PUBLIC)
# =========================

class InscriptionCreateSerializer(serializers.Serializer):
    evenement = serializers.PrimaryKeyRelatedField(
        queryset=Evenement.objects.all()
    )
    nom = serializers.CharField()
    prenom = serializers.CharField()
    email = serializers.EmailField()
    telephone = serializers.CharField()

    reponses = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )

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

            if champ.obligatoire and valeur in [None, '', []]:
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

        return data

    def create(self, validated_data):
        reponses_data = validated_data.pop('reponses')
        inscription = Inscription.objects.create(**validated_data)

        for r in reponses_data:
            champ = EvenementChamp.objects.get(id=r['champ'])
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
                reponse.valeur_fichier = valeur

            reponse.save()

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
        return [
            {
                "champ": r.champ.label,
                "type": r.champ.type,
                "valeur": (
                    r.valeur_texte or
                    r.valeur_nombre or
                    r.valeur_date or
                    r.valeur_bool or
                    str(r.valeur_fichier) if r.valeur_fichier else None
                )
            }
            for r in obj.reponses.all()
        ]
