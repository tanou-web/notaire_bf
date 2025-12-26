from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.utils import timezone

from .models import ContactInformations, ContactMessage
from .serializers import ContactInformationSerializer, ContactMessageCreateSerializer

# use the EmailService from communications
from apps.communications.services import EmailService


class ContactInformationListView(generics.ListAPIView):
	queryset = ContactInformations.objects.filter(actif=True).order_by('ordre')
	serializer_class = ContactInformationSerializer
	permission_classes = [permissions.AllowAny]


class ContactMessageCreateView(generics.CreateAPIView):
	queryset = ContactMessage.objects.all()
	serializer_class = ContactMessageCreateSerializer
	permission_classes = [permissions.AllowAny]

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		data = serializer.validated_data

		# Try to send email via existing communications service
		try:
			success, info = EmailService.send_contact_email(
				sender_email=data['email'],
				subject=data['subject'],
				message=data['message'],
				sender_name=data.get('name'),
				phone=data.get('phone')
			)
		except Exception as e:
			success = False
			info = str(e)

		# Save the contact message record with status
		instance = ContactMessage.objects.create(
			name=data.get('name', ''),
			email=data['email'],
			phone=data.get('phone'),
			subject=data['subject'],
			message=data['message'],
			sent=bool(success),
			error=None if success else str(info),
			created_at=timezone.now(),
			updated_at=timezone.now()
		)

		output_serializer = self.get_serializer(instance)

		if success:
			return Response(output_serializer.data, status=status.HTTP_201_CREATED)
		else:
			return Response({'detail': 'Erreur lors de l envoi', 'error': info}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
