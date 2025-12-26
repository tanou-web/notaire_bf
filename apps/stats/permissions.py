from rest_framework import permissions

class CanViewStats(permissions.BasePermission):
    """
    Permission personnalisée pour l'accès aux statistiques.
    Seuls les utilisateurs avec la permission appropriée peuvent voir les stats.
    """
    
    def has_permission(self, request, view):
        # L'admin peut tout voir
        if request.user.is_superuser:
            return True
        
        # Vérifier les permissions spécifiques
        return (
            request.user.has_perm('stats.view_statsvisite') or
            request.user.has_perm('stats.view_pagevue') or
            request.user.has_perm('stats.view_referent')
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission qui permet la lecture à tous,
    mais l'écriture uniquement aux admins.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user and request.user.is_staff


class CanExportStats(permissions.BasePermission):
    """Permission pour exporter les statistiques."""
    
    def has_permission(self, request, view):
        return request.user.has_perm('stats.export_stats')