from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.db.models import Q
import csv
from .models import SecurityLog, LoginAttemptLog, TokenUsageLog, AuditAdminactionlog
from .serializers import (
	SecurityLogSerializer, LoginAttemptLogSerializer,
	TokenUsageLogSerializer, AuditAdminActionSerializer
)


class IsAdmin(permissions.BasePermission):
	def has_permission(self, request, view):
		return bool(request.user and request.user.is_staff)


class SecurityLogViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = SecurityLog.objects.all()
	serializer_class = SecurityLogSerializer
	permission_classes = [permissions.IsAuthenticated, IsAdmin]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ['user', 'action', 'ip_address']
	search_fields = ['user__email', 'ip_address', 'details']
	ordering_fields = ['timestamp']

	def get_queryset(self):
		"""Support du paramètre 'q' pour la recherche générale"""
		queryset = super().get_queryset()

		search_query = self.request.query_params.get('q', None)
		if search_query:
			queryset = queryset.filter(
				Q(user__email__icontains=search_query) |
				Q(ip_address__icontains=search_query) |
				Q(action__icontains=search_query) |
				Q(details__icontains=search_query)
			)

		return queryset

	@action(detail=False, methods=['get'])
	def export(self, request):
		"""Export CSV des logs filtrés (admin only)."""
		qs = self.filter_queryset(self.get_queryset())[:10000]

		# CSV response
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename="security_logs.csv"'

		writer = csv.writer(response)
		writer.writerow(['timestamp', 'user', 'action', 'ip_address', 'status_code', 'details'])

		for log in qs:
			writer.writerow([
				log.timestamp.isoformat(),
				log.user.email if log.user else '',
				log.action,
				log.ip_address or '',
				log.status_code or '',
				json_safe(log.details)
			])

		return response


class LoginAttemptLogViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = LoginAttemptLog.objects.all()
	serializer_class = LoginAttemptLogSerializer
	permission_classes = [permissions.IsAuthenticated, IsAdmin]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ['username', 'ip_address', 'success', 'user']
	search_fields = ['username', 'user__email', 'ip_address']
	ordering_fields = ['timestamp']

	def get_queryset(self):
		"""Support du paramètre 'q' pour la recherche générale"""
		queryset = super().get_queryset()

		search_query = self.request.query_params.get('q', None)
		if search_query:
			queryset = queryset.filter(
				Q(username__icontains=search_query) |
				Q(user__email__icontains=search_query) |
				Q(ip_address__icontains=search_query)
			)

		return queryset


class TokenUsageLogViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = TokenUsageLog.objects.all()
	serializer_class = TokenUsageLogSerializer
	permission_classes = [permissions.IsAuthenticated, IsAdmin]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ['user', 'token_type', 'action']
	search_fields = ['user__email', 'token_type']
	ordering_fields = ['used_at']

	def get_queryset(self):
		"""Support du paramètre 'q' pour la recherche générale"""
		queryset = super().get_queryset()

		search_query = self.request.query_params.get('q', None)
		if search_query:
			queryset = queryset.filter(
				Q(user__email__icontains=search_query) |
				Q(token_type__icontains=search_query) |
				Q(action__icontains=search_query)
			)

		return queryset


class AuditAdminActionViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = AuditAdminactionlog.objects.all()
	serializer_class = AuditAdminActionSerializer
	permission_classes = [permissions.IsAuthenticated, IsAdmin]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = ['utilisateur', 'action', 'modele']
	search_fields = ['utilisateur__email', 'action', 'modele']
	ordering_fields = ['created_at']

	def get_queryset(self):
		"""Support du paramètre 'q' pour la recherche générale et filtrage par module"""
		queryset = super().get_queryset()

		# Support du paramètre 'q' pour la recherche générale
		search_query = self.request.query_params.get('q', None)
		if search_query:
			queryset = queryset.filter(
				Q(utilisateur__email__icontains=search_query) |
				Q(action__icontains=search_query) |
				Q(modele__icontains=search_query) |
				Q(details__icontains=search_query)
			)

		# Filtrage par module (nouveau paramètre)
		module = self.request.query_params.get('module', None)
		if module:
			queryset = queryset.filter(modele__icontains=module)

		return queryset


def json_safe(value):
	try:
		import json
		return json.dumps(value, ensure_ascii=False)
	except Exception:
		return str(value)
