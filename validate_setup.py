#!/usr/bin/env python3
"""
Validation script for olmOCR API setup
Tests image files and environment without requiring full model
"""

import os
import sys
from pathlib import Path
from PIL import Image


def check_image_file(image_path: str) -> bool:
    """Check if image file exists and is valid"""
    try:
        path = Path(image_path)
        if not path.exists():
            print(f"❌ Image not found: {image_path}")
            return False
        
        # Try to open as PIL Image
        with Image.open(path) as img:
            width, height = img.size
            mode = img.mode
            format_type = img.format
            
        print(f"✅ Valid image: {path.name}")
        print(f"   Size: {width}x{height}")
        print(f"   Mode: {mode}")
        print(f"   Format: {format_type}")
        print(f"   File size: {path.stat().st_size / 1024 / 1024:.2f} MB")
        
        # Convert to RGB if needed
        if mode != 'RGB':
            print(f"   ⚠️  Image will be converted from {mode} to RGB for processing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading image {image_path}: {str(e)}")
        return False


def check_project_structure():
    """Validate project structure"""
    required_files = [
        'app.py',
        'requirements.txt',
        'Dockerfile',
        'docker-compose.yml',
        'test_api.py',
        'README.md',
        '.gitignore'
    ]
    
    print("\n" + "="*80)
    print("PROJECT STRUCTURE VALIDATION")
    print("="*80)
    
    all_present = True
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            all_present = False
    
    return all_present


def check_docker_files():
    """Validate Docker configuration"""
    print("\n" + "="*80)
    print("DOCKER CONFIGURATION VALIDATION")
    print("="*80)
    
    # Check Dockerfile
    dockerfile = Path('Dockerfile')
    if dockerfile.exists():
        content = dockerfile.read_text()
        if 'nvidia/cuda' in content:
            print("✅ Dockerfile uses NVIDIA CUDA base image")
        if 'EXPOSE 5005' in content:
            print("✅ Dockerfile exposes port 5005")
        if 'olmOCR' in content or 'transformers' in content:
            print("✅ Dockerfile includes model dependencies")
    
    # Check docker-compose
    compose = Path('docker-compose.yml')
    if compose.exists():
        content = compose.read_text()
        if '5005:5005' in content:
            print("✅ docker-compose.yml maps port 5005")
        if 'nvidia' in content.lower():
            print("✅ docker-compose.yml configures GPU support")
        if 'huggingface_cache' in content:
            print("✅ docker-compose.yml includes model cache volume")
    
    return True


def check_python_environment():
    """Check Python environment"""
    print("\n" + "="*80)
    print("PYTHON ENVIRONMENT")
    print("="*80)
    
    print(f"✅ Python version: {sys.version}")
    
    # Check for key packages
    packages = [
        ('torch', 'PyTorch'),
        ('PIL', 'Pillow'),
        ('transformers', 'Transformers'),
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn')
    ]
    
    for module, name in packages:
        try:
            __import__(module)
            print(f"✅ {name} installed")
        except ImportError:
            print(f"⚠️  {name} not installed (will be in Docker)")
    
    # Check for CUDA
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA available: {torch.cuda.get_device_name(0)}")
            print(f"   CUDA version: {torch.version.cuda}")
            print(f"   GPU count: {torch.cuda.device_count()}")
        else:
            print("⚠️  CUDA not available (will run on CPU or in Docker)")
    except ImportError:
        print("⚠️  PyTorch not installed (will be in Docker)")
    
    return True


def main():
    """Run all validation checks"""
    print("="*80)
    print("olmOCR API - Setup Validation")
    print("="*80)
    
    # Test images
    test_images = [
        r"C:\Users\alexa\OneDrive\Pictures\Samsung Gallery\Pictures\Office Lens\vettest.jpg",
        r"C:\Users\alexa\OneDrive\Pictures\grandmatest.jpg"
    ]
    
    print("\n" + "="*80)
    print("TEST IMAGES VALIDATION")
    print("="*80)
    
    images_valid = True
    for img_path in test_images:
        print(f"\nChecking: {img_path}")
        if not check_image_file(img_path):
            images_valid = False
    
    # Project structure
    structure_valid = check_project_structure()
    
    # Docker files
    docker_valid = check_docker_files()
    
    # Python environment
    python_valid = check_python_environment()
    
    # Git status
    print("\n" + "="*80)
    print("GIT REPOSITORY")
    print("="*80)
    if Path('.git').exists():
        print("✅ Git repository initialized")
        try:
            import subprocess
            result = subprocess.run(['git', 'log', '--oneline', '-1'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Last commit: {result.stdout.strip()}")
        except:
            pass
    else:
        print("❌ Git repository not initialized")
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    checks = {
        "Test Images": images_valid,
        "Project Structure": structure_valid,
        "Docker Configuration": docker_valid,
        "Python Environment": python_valid
    }
    
    for check_name, status in checks.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {check_name}")
    
    if all(checks.values()):
        print("\n" + "="*80)
        print("🎉 ALL CHECKS PASSED!")
        print("="*80)
        print("\nNext steps:")
        print("1. Build Docker image: docker build -t olmocr-api .")
        print("2. Push to Docker Hub: ./build_and_push.sh")
        print("3. Deploy to Portainer using docker-compose.yml")
        print("4. Test API: python test_api.py <image_path>")
        return 0
    else:
        print("\n" + "="*80)
        print("⚠️  SOME CHECKS FAILED")
        print("="*80)
        print("Review the issues above before deployment")
        return 1


if __name__ == "__main__":
    sys.exit(main())

