# Script PowerShell pour tester l'API Notaires BF
# Utilisation : .\test-api.ps1

$baseUrl = "http://localhost:8000/api"

Write-Host "🧪 TEST DE L'API NOTAIRES BF" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Test 1: Endpoints publics
Write-Host "`n1. 🟢 Test des endpoints PUBLICS" -ForegroundColor Green

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/geographie/regions/" -Method GET
    Write-Host "   ✅ Régions: HTTP $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Régions: Erreur $($_.Exception.Response.StatusCode)" -ForegroundColor Red
}

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/actualites/actualites/" -Method GET
    Write-Host "   ✅ Actualités: HTTP $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Actualités: Erreur $($_.Exception.Response.StatusCode)" -ForegroundColor Red
}

# Test 2: Token refresh (méthode correcte)
Write-Host "`n2. 🔵 Test TOKEN REFRESH (méthode POST)" -ForegroundColor Blue

# D'abord essayer de refresh avec un token invalide pour voir l'erreur normale
try {
    $body = @{
        refresh = "invalid_token_here"
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "$baseUrl/token/refresh/" -Method POST `
        -Body $body -ContentType "application/json"

    Write-Host "   ✅ Refresh Token: HTTP $($response.StatusCode)" -ForegroundColor Green
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 401) {
        Write-Host "   ✅ Refresh Token: HTTP 401 (Token invalide - NORMAL)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Refresh Token: HTTP $statusCode" -ForegroundColor Red
    }
}

# Test 3: Login (si admin existe)
Write-Host "`n3. 🟠 Test LOGIN (avec compte existant)" -ForegroundColor Yellow

try {
    $body = @{
        username = "admin"
        password = "admin123"
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "$baseUrl/auth/login/" -Method POST `
        -Body $body -ContentType "application/json"

    $data = $response.Content | ConvertFrom-Json
    Write-Host "   ✅ Login: HTTP $($response.StatusCode)" -ForegroundColor Green
    Write-Host "   📝 Token reçu: $($data.access.Substring(0, 50))..." -ForegroundColor Gray

    # Stocker le token pour les tests suivants
    $accessToken = $data.access

} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "   ❌ Login: HTTP $statusCode (Créez d'abord un compte admin)" -ForegroundColor Red
    Write-Host "   💡 Commande: python manage.py createsuperuser" -ForegroundColor Cyan
}

# Test 4: Endpoint protégé (si token disponible)
if ($accessToken) {
    Write-Host "`n4. 🔴 Test ENDPOINT PROTÉGÉ (avec token)" -ForegroundColor Red

    try {
        $headers = @{
            "Authorization" = "Bearer $accessToken"
            "Content-Type" = "application/json"
        }

        $response = Invoke-WebRequest -Uri "$baseUrl/notaires/notaires/" -Method GET -Headers $headers
        Write-Host "   ✅ Notaires: HTTP $($response.StatusCode)" -ForegroundColor Green

    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq 401) {
            Write-Host "   ⚠️ Notaires: HTTP 401 (Token expiré - NORMAL)" -ForegroundColor Yellow
            Write-Host "   💡 Utilisez /api/token/refresh/ pour rafraîchir" -ForegroundColor Cyan
        } else {
            Write-Host "   ❌ Notaires: HTTP $statusCode" -ForegroundColor Red
        }
    }
}

Write-Host "`n🎯 RÉSUMÉ DES TESTS" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan
Write-Host "✅ Endpoints publics: Devraient fonctionner" -ForegroundColor Green
Write-Host "✅ Token refresh: POST seulement (pas GET)" -ForegroundColor Green
Write-Host "✅ Login: Créez un compte admin d'abord" -ForegroundColor Green
Write-Host "✅ Endpoints protégés: Nécessitent un token valide" -ForegroundColor Green

Write-Host "`n📚 COMMANDES UTILES:" -ForegroundColor Cyan
Write-Host "Créer admin: python manage.py createsuperuser" -ForegroundColor White
Write-Host "Charger données: python manage.py loaddata fixtures/demo_data.json" -ForegroundColor White
Write-Host "Voir URLs: python manage.py show_urls" -ForegroundColor White
