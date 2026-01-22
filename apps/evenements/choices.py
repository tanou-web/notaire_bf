from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def choix_statuts(request):
    return Response({
        "evenement": {
            "statuts": [
                {"value": "brouillon", "label": "Brouillon"},
                {"value": "ouvert", "label": "Ouvert"},
                {"value": "complet", "label": "Complet"},
                {"value": "termine", "label": "Terminé"},
                {"value": "annule", "label": "Annulé"}
            ]
        },
        "inscription": {
            "statuts": [
                {"value": "en_attente", "label": "En attente"},
                {"value": "validee", "label": "Validée"},
                {"value": "refusee", "label": "Refusée"},
                {"value": "annulee", "label": "Annulée"}
            ]
        }
    })
