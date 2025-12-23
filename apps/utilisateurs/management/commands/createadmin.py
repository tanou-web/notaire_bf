from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import getpass

User = get_user_model()

class Command(BaseCommand):
    help = 'Crée un superutilisateur avec toutes les informations nécessaires'
    
    def add_arguments(self, parser):
        parser.add_argument('--username', help="Nom d'utilisateur")
        parser.add_argument('--email', help="Email")
        parser.add_argument('--password', help="Mot de passe")
    
    def handle(self, *args, **options):
        # Demander les informations si non fournies
        username = options['username'] or input("Username: ")
        email = options['email'] or input("Email: ")
        password = options['password'] or getpass.getpass("Password: ")
        
        # Informations supplémentaires
        nom = input("Nom: ") or "Admin"
        prenom = input("Prénom: ") or "System"
        telephone = input("Téléphone (+226...): ") or "+22600000000"
        
        try:
            # Vérifier si l'utilisateur existe déjà
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.ERROR(f"L'utilisateur '{username}' existe déjà."))
                return
            
            if User.objects.filter(email=email).exists():
                self.stdout.write(self.style.ERROR(f"L'email '{email}' est déjà utilisé."))
                return
            
            # Créer le superutilisateur
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                nom=nom,
                prenom=prenom,
                telephone=telephone,
                is_active=True,
                email_verifie=True,
                telephone_verifie=True
            )
            
            self.stdout.write(self.style.SUCCESS(
                f"Superutilisateur créé avec succès!\n"
                f"   Username: {user.username}\n"
                f"   Email: {user.email}\n"
                f"   Nom: {user.nom} {user.prenom}\n"
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur: {e}"))