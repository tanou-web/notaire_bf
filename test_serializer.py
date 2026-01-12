import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')
django.setup()

from apps.utilisateurs.serializers import AdminCreateSerializer
from apps.utilisateurs.models import User

# Tester la validation du serializer
data = {
    'username': 'test_admin',
    'email': 'test@example.com',
    'password': 'Test123!@#',
    'password_confirmation': 'Test123!@#',
    'nom': 'Test',
    'prenom': 'Admin',
    'telephone': '+22670000001',
    'is_staff': True,
    'is_superuser': True
}

print("=== Test AdminCreateSerializer ===")
serializer = AdminCreateSerializer(data=data)
print('Serializer valide:', serializer.is_valid())
if not serializer.is_valid():
    print('Erreurs:', serializer.errors)
else:
    print('Données validées:', serializer.validated_data)

# Tester UserSerializer
from apps.utilisateurs.serializers import UserSerializer
print("\n=== Test UserSerializer ===")
user_serializer = UserSerializer(data=data)
print('UserSerializer valide:', user_serializer.is_valid())
if not user_serializer.is_valid():
    print('Erreurs UserSerializer:', user_serializer.errors)
else:
    print('Données UserSerializer validées:', user_serializer.validated_data)