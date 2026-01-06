from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée pour n'autoriser que le propriétaire à modifier un objet
    """
    def has_object_permission(self, request, view, obj):
        # Les méthodes sécurisées sont toujours autorisées
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # L'écriture n'est autorisée que pour le propriétaire
        return obj == request.user

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission qui permet aux administrateurs de tout faire,
    aux autres utilisateurs seulement la lecture
    """
    def has_permission(self, request, view):
        # Les méthodes sécurisées sont autorisées pour tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # L'écriture n'est autorisée qu'aux administrateurs
        return request.user and request.user.is_staff

class IsNotairePermission(permissions.BasePermission):
    """
    Permission pour les notaires
    """
    def has_permission(self, request, view):
        # Vérifier si l'utilisateur est un notaire
        if hasattr(request.user, 'notaire_profile'):
            return True
        return False
 
    

class IsSuperUser(permissions.BasePermission):
    
   # Permission qui n'autorise que les superutilisateurs.
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)

class IsAdminUser(permissions.BasePermission):
    
    #Permission qui autorise les administrateurs (staff) et superutilisateurs.
    
    def has_permission(self, request, view):
        return bool(request.user and (request.user.is_staff or request.user.is_superuser))

class IsOwnerOrAdmin(permissions.BasePermission):

    #Permission qui autorise le propriétaire ou les administrateurs.

    def has_object_permission(self, request, view, obj):
        # Les administrateurs peuvent tout faire
        if request.user and (request.user.is_staff or request.user.is_superuser):
            return True

        # L'utilisateur peut modifier son propre objet
        return obj == request.user

class IsNotaireOrAdmin(permissions.BasePermission):
    """
    Permission qui autorise :
    - Le notaire lui-même à accéder à ses propres données
    - Les administrateurs à accéder à toutes les données des notaires
    """

    def has_object_permission(self, request, view, obj):
        # Les administrateurs peuvent tout faire
        if request.user and (request.user.is_staff or request.user.is_superuser):
            return True

        # Vérifier si l'utilisateur est le notaire concerné
        if hasattr(request.user, 'notaire_profile') and request.user.notaire_profile == obj:
            return True

        return False