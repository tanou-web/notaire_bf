from rest_framework import serializers
from .models import (
    Evenement,
    Inscription,
    InscriptionReponse,
    EvenementChamp
)

# serializers.py
from rest_framework import serializers
from .models import Evenement, EvenementChamp, Inscription, InscriptionReponse

class EvenementChampSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvenementChamp
        fields = ['id', 'label', 'type', 'obligatoire', 'options', 'ordre']

class EvenementSerializer(serializers.ModelSerializer):
    champs = EvenementChampSerializer(many=True, read_only=True)

    class Meta:
        model = Evenement
        fields = ['id', 'titre', 'description', 'actif', 'created_at', 'champs']

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

    # 🔐 VALIDATION FORTE
    def validate(self, data):
        evenement = data['evenement']
        reponses = data['reponses']

        champs = EvenementChamp.objects.filter(
            evenement=evenement,
            actif=True
        )

        champs_map = {c.id: c for c in champs}

        champs_obligatoires = {
            c.id for c in champs if c.obligatoire
        }

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

    # 💾 ENREGISTREMENT
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

class InscriptionSerializer(serializers.ModelSerializer):
    reponses = serializers.SerializerMethodField()

    class Meta:
        model = Inscription
        fields = ['id', 'evenement', 'nom', 'prenom', 'email', 'telephone', 'created_at', 'reponses']

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
            } for r in obj.reponses.all()
        ]
