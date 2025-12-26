from rest_framework import serializers
from .models import ConseilsConseildujour


class ConseilDuJourSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConseilsConseildujour
        fields = ['id', 'conseil', 'date', 'actif', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_date(self, value):
        """Ensure there's no other conseil for the same date.

        When updating, exclude the current instance from the check.
        """
        qs = ConseilsConseildujour.objects.filter(date=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Un conseil pour cette date existe déjà.")
        return value
