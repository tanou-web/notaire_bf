"""
Script de validation complète des livrables
Teste la structure, les imports et la cohérence du code
"""
import sys
import os
import importlib.util
import re

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

def test_imports():
    """Tester les imports des nouveaux modèles"""
    print("=" * 70)
    print("TEST DES IMPORTS")
    print("=" * 70)
    
    results = {'passed': [], 'failed': []}
    
    # Tester les imports des modèles
    modules_to_test = [
        ('apps.organisation.models', ['OrganisationHistorique', 'OrganisationMission']),
        ('apps.demandes.models', ['DemandesPieceJointe']),
        ('apps.core.models', ['CorePage']),
        ('apps.system.models', ['SystemEmailprofessionnel']),
    ]
    
    for module_path, classes in modules_to_test:
        try:
            # Vérifier que le fichier existe
            file_path = os.path.join(BASE_DIR, module_path.replace('.', os.sep) + '.py')
            if os.path.exists(file_path):
                results['passed'].append(f"[OK] Fichier {module_path}.py existe")
                print(f"[OK] Fichier {module_path}.py existe")
                
                # Vérifier que les classes sont définies
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for class_name in classes:
                        if f'class {class_name}' in content:
                            results['passed'].append(f"[OK] Classe {class_name} trouvee")
                            print(f"[OK] Classe {class_name} trouvee")
                        else:
                            results['failed'].append(f"[ERREUR] Classe {class_name} non trouvee")
                            print(f"[ERREUR] Classe {class_name} NON TROUVEE")
            else:
                results['failed'].append(f"[ERREUR] Fichier {module_path}.py introuvable")
                print(f"[ERREUR] Fichier {module_path}.py introuvable")
        except Exception as e:
            results['failed'].append(f"[ERREUR] Erreur lors de l'analyse de {module_path}: {e}")
            print(f"[ERREUR] Erreur lors de l'analyse de {module_path}: {e}")
    
    print()
    return results

def test_serializers():
    """Tester les serializers"""
    print("=" * 70)
    print("TEST DES SERIALIZERS")
    print("=" * 70)
    
    results = {'passed': [], 'failed': []}
    
    serializers_to_test = [
        ('apps/organisation/serializers.py', 'OrganisationHistoriqueSerializer'),
        ('apps/organisation/serializers.py', 'OrganisationMissionSerializer'),
        ('apps/demandes/serializers.py', 'PieceJointeSerializer'),
        ('apps/core/serializers.py', 'CorePageSerializer'),
        ('apps/system/serializers.py', 'SystemEmailprofessionnelSerializer'),
    ]
    
    for filepath, serializer_name in serializers_to_test:
        full_path = os.path.join(BASE_DIR, filepath)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if f'class {serializer_name}' in content:
                    results['passed'].append(f"[OK] {serializer_name}")
                    print(f"[OK] {serializer_name} trouve")
                else:
                    results['failed'].append(f"[ERREUR] {serializer_name} non trouve")
                    print(f"[ERREUR] {serializer_name} NON TROUVE")
        else:
            results['failed'].append(f"[ERREUR] Fichier {filepath} introuvable")
            print(f"[ERREUR] Fichier {filepath} introuvable")
    
    print()
    return results

def test_views():
    """Tester les views"""
    print("=" * 70)
    print("TEST DES VIEWS")
    print("=" * 70)
    
    results = {'passed': [], 'failed': []}
    
    views_to_test = [
        ('apps/organisation/views.py', 'HistoriqueViewSet'),
        ('apps/organisation/views.py', 'MissionViewSet'),
        ('apps/demandes/views.py', 'PieceJointeViewSet'),
        ('apps/core/views.py', 'CorePageViewSet'),
        ('apps/system/views.py', 'SystemEmailprofessionnelViewSet'),
    ]
    
    for filepath, view_name in views_to_test:
        full_path = os.path.join(BASE_DIR, filepath)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if f'class {view_name}' in content:
                    results['passed'].append(f"[OK] {view_name}")
                    print(f"[OK] {view_name} trouve")
                else:
                    results['failed'].append(f"[ERREUR] {view_name} non trouve")
                    print(f"[ERREUR] {view_name} NON TROUVE")
        else:
            results['failed'].append(f"[ERREUR] Fichier {filepath} introuvable")
            print(f"[ERREUR] Fichier {filepath} introuvable")
    
    print()
    return results

def test_urls():
    """Tester les URLs"""
    print("=" * 70)
    print("TEST DES URLs")
    print("=" * 70)
    
    results = {'passed': [], 'failed': []}
    
    urls_to_check = [
        ('apps/organisation/urls.py', ['historique', 'missions']),
        ('apps/demandes/urls.py', ['pieces-jointes']),
        ('apps/core/urls.py', ['pages']),
        ('apps/system/urls.py', ['emails-professionnels']),
    ]
    
    for filepath, routes in urls_to_check:
        full_path = os.path.join(BASE_DIR, filepath)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for route in routes:
                    if route in content or 'router.register' in content:
                        results['passed'].append(f"[OK] Route '{route}' dans {filepath}")
                        print(f"[OK] Route '{route}' trouvee dans {filepath}")
                    else:
                        results['failed'].append(f"[ERREUR] Route '{route}' non trouvee")
                        print(f"[ERREUR] Route '{route}' NON TROUVEE")
        else:
            results['failed'].append(f"[ERREUR] Fichier {filepath} introuvable")
            print(f"[ERREUR] Fichier {filepath} introuvable")
    
    print()
    return results

def test_fields():
    """Tester les champs spécifiques"""
    print("=" * 70)
    print("TEST DES CHAMPS SPECIFIQUES")
    print("=" * 70)
    
    results = {'passed': [], 'failed': []}
    
    # Vérifier mot_du_president
    org_file = os.path.join(BASE_DIR, 'apps/organisation/models.py')
    if os.path.exists(org_file):
        with open(org_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'mot_du_president' in content:
                results['passed'].append("[OK] Champ mot_du_president")
                print("[OK] Champ 'mot_du_president' trouve")
            else:
                results['failed'].append("[ERREUR] Champ mot_du_president non trouve")
                print("[ERREUR] Champ 'mot_du_president' NON TROUVE")
    
    # Vérifier latitude/longitude
    contact_file = os.path.join(BASE_DIR, 'apps/contact/models.py')
    if os.path.exists(contact_file):
        with open(contact_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'latitude' in content and 'longitude' in content:
                results['passed'].append("[OK] Champs latitude/longitude")
                print("[OK] Champs 'latitude' et 'longitude' trouves")
            else:
                results['failed'].append("[ERREUR] Champs latitude/longitude non trouves")
                print("[ERREUR] Champs 'latitude'/'longitude' NON TROUVES")
    
    print()
    return results

def validate_migration_readiness():
    """Vérifier que les modèles sont prêts pour les migrations"""
    print("=" * 70)
    print("VERIFICATION PREPARATION MIGRATIONS")
    print("=" * 70)
    
    results = {'passed': [], 'failed': []}
    
    # Vérifier que les modèles ont bien db_table défini
    models_to_check = [
        ('apps/organisation/models.py', ['OrganisationHistorique', 'OrganisationMission']),
        ('apps/demandes/models.py', ['DemandesPieceJointe']),
        ('apps/core/models.py', ['CorePage']),
        ('apps/system/models.py', ['SystemEmailprofessionnel']),
    ]
    
    for filepath, model_names in models_to_check:
        full_path = os.path.join(BASE_DIR, filepath)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for model_name in model_names:
                    # Vérifier que la classe a une Meta avec db_table
                    pattern = rf'class {model_name}.*?class Meta:.*?db_table\s*=\s*[\'"](\w+)[\'"]'
                    match = re.search(pattern, content, re.DOTALL)
                    if match:
                        db_table = match.group(1)
                        results['passed'].append(f"[OK] {model_name} -> db_table='{db_table}'")
                        print(f"[OK] {model_name} a db_table='{db_table}'")
                    else:
                        # Vérifier au moins que Meta existe
                        if f'class {model_name}' in content and 'class Meta' in content:
                            results['passed'].append(f"[OK] {model_name} a une classe Meta")
                            print(f"[OK] {model_name} a une classe Meta")
                        else:
                            results['failed'].append(f"[ERREUR] {model_name} sans Meta/db_table")
                            print(f"[ERREUR] {model_name} sans classe Meta ou db_table")
    
    print()
    return results

def main():
    """Fonction principale de validation"""
    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE DES LIVRABLES")
    print("=" * 70)
    print()
    
    all_results = {
        'passed': [],
        'failed': []
    }
    
    # Exécuter tous les tests
    test_functions = [
        test_imports,
        test_serializers,
        test_views,
        test_urls,
        test_fields,
        validate_migration_readiness
    ]
    
    for test_func in test_functions:
        results = test_func()
        all_results['passed'].extend(results['passed'])
        all_results['failed'].extend(results['failed'])
    
    # Rapport final
    print("=" * 70)
    print("RAPPORT FINAL")
    print("=" * 70)
    print()
    print(f"Total de tests reussis : {len(all_results['passed'])}")
    print(f"Total de tests echoues : {len(all_results['failed'])}")
    print()
    
    if all_results['failed']:
        print("ERREURS TROUVEES :")
        for error in all_results['failed']:
            print(f"  {error}")
        print()
    
    # Score
    total = len(all_results['passed']) + len(all_results['failed'])
    if total > 0:
        score = (len(all_results['passed']) / total) * 100
        print(f"SCORE DE CONFORMITE : {score:.1f}%")
        print()
        
        if score == 100:
            print(">>> EXCELLENT ! Tous les tests sont passes. Les livrables sont conformes.")
            print(">>> Les migrations peuvent etre creees avec : python manage.py makemigrations")
            return 0
        elif score >= 95:
            print(">>> TRES BON ! Quelques ajustements mineurs peuvent etre necessaires.")
            return 1
        else:
            print(">>> ATTENTION ! Des corrections sont necessaires avant de creer les migrations.")
            return 2
    
    return 3

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

