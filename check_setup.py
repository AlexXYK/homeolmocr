#!/usr/bin/env python3
"""
Simple validation script without external dependencies
"""

import os
import sys
from pathlib import Path


def check_file_exists(filepath):
    """Check if a file exists"""
    path = Path(filepath)
    if path.exists():
        size_mb = path.stat().st_size / 1024 / 1024
        print(f"✅ Found: {path.name} ({size_mb:.2f} MB)")
        return True
    else:
        print(f"❌ Not found: {filepath}")
        return False


def main():
    print("="*80)
    print("olmOCR API - Setup Validation")
    print("="*80)
    
    # Check test images
    print("\n📸 TEST IMAGES:")
    test_images = [
        r"C:\Users\alexa\OneDrive\Pictures\Samsung Gallery\Pictures\Office Lens\vettest.jpg",
        r"C:\Users\alexa\OneDrive\Pictures\grandmatest.jpg"
    ]
    
    images_ok = all(check_file_exists(img) for img in test_images)
    
    # Check project files
    print("\n📁 PROJECT FILES:")
    project_files = [
        'app.py',
        'requirements.txt',
        'Dockerfile',
        'docker-compose.yml',
        'test_api.py',
        'README.md',
        '.gitignore',
        'entrypoint.sh'
    ]
    
    files_ok = all(check_file_exists(f) for f in project_files)
    
    # Check git
    print("\n🔧 GIT REPOSITORY:")
    git_ok = Path('.git').exists()
    if git_ok:
        print("✅ Git repository initialized")
    else:
        print("❌ Git repository not initialized")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY:")
    print("="*80)
    print(f"{'✅' if images_ok else '❌'} Test images")
    print(f"{'✅' if files_ok else '❌'} Project files")
    print(f"{'✅' if git_ok else '❌'} Git repository")
    
    if images_ok and files_ok and git_ok:
        print("\n🎉 Setup looks good!")
        print("\n📝 Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Build Docker: docker build -t olmocr-api .")
        print("3. Test locally: docker run --gpus all -p 5005:5005 olmocr-api")
        print("4. Push to Docker Hub: docker push yourusername/olmocr-api:latest")
        print("5. Deploy via Portainer using docker-compose.yml")
        return 0
    else:
        print("\n⚠️  Some issues found. Please check above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

