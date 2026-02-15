# Directives Techniques : Section Ventes & Reçus de Stickers

Ce document résume le fonctionnement de l'API des stickers après la mise à jour du système de recherche par référence.

## 1. Modèles de Données

Il existe deux types de ventes distincts :
- **`VenteSticker`** : Ventes effectuées par les notaires aux clients finaux.
  - Références : `VEN-YYYYMMDD-XXXXXX`
- **`VenteStickerNotaire`** : Ventes de stock effectuées par l'ONBF aux notaires.
  - Références : `VNT-YYYYMMDD-XXXXXX`

## 2. Endpoints Clés

### Reçus (Endpoint Unifié)
**GET** `/api/ventes/stickers/{reference}/recu/`

Cet endpoint est intelligent. Il tente de trouver la vente dans cet ordre :
1. Recherche dans `VenteSticker` (Ventes clients).
2. Si non trouvé et que la référence commence par `VNT`, recherche dans `VenteStickerNotaire` (Ventes notaires).

### Ventes aux Notaires (Gestion de Stock)
**GET/PATCH/DELETE** `/api/ventes/ventes-stickers-notaires/{reference}/`
- Permet la gestion par référence (`VNT-...`) grâce à `lookup_field = 'reference'`.

### Reçus Spécifiques (Admin)
**GET** `/api/ventes/recus-stickers/{reference}/`
- Accès direct aux données du reçu pour les ventes aux notaires.

## 3. Directives de Développement

> [!IMPORTANT]
> **Recherche par Référence** : Dans Django Rest Framework, pour utiliser une chaîne (comme `VNT-123`) au lieu d'un ID numérique dans l'URL, le ViewSet **doit** contenir :
> ```python
> lookup_field = 'reference'
> ```

> [!TIP]
> **Uniformité des Reçus** : Les serializers `RecuVenteStickerSerializer` (pour `VEN-`) et `RecuStickerSerializer` (pour `VNT-`) ont été harmonisés pour renvoyer des structures de données similaires au frontend, facilitant la génération de PDF.

## 4. Tests et Débogage
En cas d'erreur 404 sur une référence existante, vérifiez :
1. Si le préfixe (`VEN-` ou `VNT-`) correspond à la table interrogée.
2. Si le `lookup_field` est bien présent dans la Vue associée dans `views.py`.
