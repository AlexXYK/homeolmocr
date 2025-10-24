#!/usr/bin/env python3
"""
Test script for olmOCR API
"""

import sys
import requests
import json
from pathlib import Path


def test_ocr(image_path: str, api_url: str = "http://localhost:5005"):
    """
    Test the OCR API with an image file
    
    Args:
        image_path: Path to the image file
        api_url: Base URL of the API
    """
    # Check if file exists
    img_path = Path(image_path)
    if not img_path.exists():
        print(f"❌ Error: Image file not found: {image_path}")
        return False
    
    print(f"📸 Testing OCR with: {img_path.name}")
    print(f"🌐 API URL: {api_url}")
    
    # Test health endpoint first
    try:
        print("\n🔍 Checking API health...")
        health_response = requests.get(f"{api_url}/health", timeout=5)
        health_data = health_response.json()
        print(f"✅ Health check: {json.dumps(health_data, indent=2)}")
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False
    
    # Test OCR endpoint
    try:
        print(f"\n🚀 Sending image for OCR processing...")
        with open(img_path, 'rb') as f:
            files = {'file': (img_path.name, f, 'image/jpeg')}
            response = requests.post(
                f"{api_url}/ocr",
                files=files,
                timeout=300  # 5 minutes timeout for processing
            )
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        
        if result.get('success'):
            print("✅ OCR processing successful!\n")
            print("=" * 80)
            print("EXTRACTED TEXT:")
            print("=" * 80)
            print(result.get('text', 'No text extracted'))
            print("=" * 80)
            
            if result.get('metadata'):
                print("\n📊 Metadata:")
                print(json.dumps(result['metadata'], indent=2))
            
            # Save output to file
            output_file = img_path.parent / f"{img_path.stem}_ocr.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.get('text', ''))
            print(f"\n💾 Output saved to: {output_file}")
            
            return True
        else:
            print(f"❌ OCR processing failed: {result.get('error', 'Unknown error')}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out. The image might be too large or complex.")
        return False
    except Exception as e:
        print(f"❌ Error during OCR request: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <image_path> [api_url]")
        print("Example: python test_api.py test_image.jpg")
        print("Example: python test_api.py test_image.jpg http://localhost:5005")
        sys.exit(1)
    
    image_path = sys.argv[1]
    api_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:5005"
    
    success = test_ocr(image_path, api_url)
    sys.exit(0 if success else 1)

