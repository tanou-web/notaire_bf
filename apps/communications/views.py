from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from .serializers import ContactSerializer, CommunicationsEmailLogSerializer
from .services import EmailService
from .models import CommunicationsEmaillog


class ContactAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        name = data.get('name')
        email = data['email']
        phone = data.get('phone')
        subject = data['subject']
        message = data['message']

        success, info = EmailService.send_contact_email(
            sender_email=email,
            subject=subject,
            message=message,
            sender_name=name,
            phone=phone
        )

        # determine recipients for logging
        recipients = getattr(settings, 'CONTACT_RECIPIENTS', None) or getattr(settings, 'CONTACT_EMAILS', None)
        if not recipients:
            admins = getattr(settings, 'ADMINS', None)
            if admins:
                recipients = [a[1] for a in admins]
            else:
                recipients = [getattr(settings, 'DEFAULT_FROM_EMAIL', '')]

        # Save log entry
        try:
            log = CommunicationsEmaillog(
                type_email='contact',
                destinataire=','.join(recipients),
                sujet=subject,
                contenu=message,
                statut='sent' if success else 'failed',
                message_id=info if success else None,
                erreur=None if success else str(info),
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            # If the underlying DB requires managed False, this will still attempt to save
            log.save()
        except Exception:
            # avoid failing the entire request if logging fails
            pass

        if success:
            return Response({'detail': 'Message envoyé'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': 'Erreur lors de l envoi', 'error': info}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommunicationsEmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    queryset = CommunicationsEmaillog.objects.all().order_by('-created_at')
    serializer_class = CommunicationsEmailLogSerializer
