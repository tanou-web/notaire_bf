# find_admin.py
import os
import sys

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')

try:
    import django
    django.setup()
    
    print("🔍 Recherche des fichiers admin.py problématiques...")
    print("=" * 60)
    
    # 1. Lister tous les admin.py
    admin_files = []
    for root, dirs, files in os.walk('apps'):
        for file in files:
            if file == 'admin.py':
                full_path = os.path.join(root, file)
                admin_files.append(full_path)
    
    print(f"📁 {len(admin_files)} fichiers admin.py trouvés:")
    for f in admin_files:
        print(f"  • {f}")
    
    print("\n🔧 Test d'import de chaque admin.py...")
    
    # 2. Tester chaque admin.py
    problematic_files = []
    for admin_file in admin_files:
        try:
            # Convertir le chemin en module Python
            rel_path = os.path.relpath(admin_file, 'apps')
            module_path = rel_path.replace('\\', '.').replace('/', '.').replace('.py', '')
            full_module = f"apps.{module_path}"
            
            # Essayer d'importer
            __import__(full_module)
            print(f"  ✅ {admin_file} - OK")
        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ {admin_file} - ERREUR: {error_msg[:100]}...")
            problematic_files.append((admin_file, e))
    
    # 3. Afficher les détails des fichiers problématiques
    if problematic_files:
        print("\n🚨 FICHIERS ADMIN.PY PROBLÉMATIQUES :")
        print("=" * 60)
        for file_path, error in problematic_files:
            print(f"\n📄 {file_path}")
            print(f"   Erreur: {error}")
            
            # Afficher le contenu du fichier
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Chercher la ligne avec 'actions ='
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'actions =' in line:
                            print(f"   Ligne {i+1}: {line.strip()}")
            except:
                pass
    
except Exception as e:
    print(f"❌ Erreur générale: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)