#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path
from io import BytesIO
from django.core.files.base import ContentFile

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notaires_bf.settings')

def check_pillow():
    print("\n=== STEP 1: CHECK PILLOW ===")
    try:
        from PIL import Image
        print(f"✅ Pillow is installed. Version: {Image.__version__ if hasattr(Image, '__version__') else 'unknown'}")
        
        # Test basic image operations
        img = Image.new('RGB', (100, 100), color = (73, 109, 137))
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        print("✅ Pillow: Successfully created and saved a dummy JPEG image to memory buffer.")
        return True
    except ImportError:
        print("❌ Pillow is NOT installed.")
        return False
    except Exception as e:
        print(f"❌ Pillow Error: {str(e)}")
        return False

def check_storage_config():
    print("\n=== STEP 2: CHECK STORAGE CONFIG ===")
    from django.conf import settings
    
    print(f"DEBUG status: {settings.DEBUG}")
    
    # Check default storage
    from django.core.files.storage import default_storage
    print(f"Default storage backend: {default_storage.__class__.__name__}")
    
    # Check MEDIA settings
    print(f"MEDIA_URL: {settings.MEDIA_URL}")
    if hasattr(settings, 'MEDIA_ROOT'):
        print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
        print(f"MEDIA_ROOT exists: {os.path.exists(settings.MEDIA_ROOT)}")
        if os.path.exists(settings.MEDIA_ROOT):
            print(f"MEDIA_ROOT is writable: {os.access(settings.MEDIA_ROOT, os.W_OK)}")
    else:
        print("MEDIA_ROOT: Not defined (likely using remote storage)")

    # Check for S3/Cloudinary variables if not debug
    if not settings.DEBUG:
        print("\nProduction Storage Variables Check:")
        provider = os.getenv('STORAGE_PROVIDER', 's3')
        print(f"STORAGE_PROVIDER: {provider}")
        
        if provider == 's3':
            keys = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_STORAGE_BUCKET_NAME']
            for key in keys:
                val = os.getenv(key)
                print(f"{key}: {'SET (length ' + str(len(val)) + ')' if val else 'MISSING'}")
        elif provider == 'cloudinary':
            keys = ['CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET']
            for key in keys:
                val = os.getenv(key)
                print(f"{key}: {'SET (length ' + str(len(val)) + ')' if val else 'MISSING'}")

def test_file_save():
    print("\n=== STEP 3: TEST FILE SAVE ===")
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    
    test_content = b"This is a test file content."
    test_name = "test_diagnostic_file.txt"
    
    try:
        path = default_storage.save(test_name, ContentFile(test_content))
        print(f"✅ Successfully saved test file to: {path}")
        
        # Try to read it back
        if default_storage.exists(path):
            with default_storage.open(path) as f:
                content = f.read()
                if content == test_content:
                    print("✅ Successfully read back the test file content.")
                else:
                    print("❌ Content mismatch after reading back.")
            
            # Delete it
            default_storage.delete(path)
            print("✅ Successfully deleted test file.")
        else:
            print("❌ File was saved but doesn't exist according to storage backend.")
            
    except Exception as e:
        print(f"❌ Error during file save test: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    try:
        django.setup()
        print("✅ Django setup successful.")
    except Exception as e:
        print(f"❌ Django setup failed: {str(e)}")
        return

    check_pillow()
    check_storage_config()
    test_file_save()

if __name__ == "__main__":
    main()
