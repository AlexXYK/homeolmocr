#!/usr/bin/env python3
"""
Example usage scripts for olmOCR API
"""

import requests
import json
from pathlib import Path


def example_simple_ocr(image_path: str, api_url: str = "http://localhost:5005"):
    """
    Simplest example: Send image, get text
    """
    with open(image_path, 'rb') as f:
        response = requests.post(
            f"{api_url}/ocr",
            files={'file': f}
        )
    
    result = response.json()
    if result['success']:
        return result['text']
    else:
        raise Exception(result['error'])


def example_with_error_handling(image_path: str, api_url: str = "http://localhost:5005"):
    """
    Example with proper error handling
    """
    try:
        # Check health first
        health = requests.get(f"{api_url}/health", timeout=5)
        if not health.ok:
            raise Exception("API is not healthy")
        
        # Process image
        with open(image_path, 'rb') as f:
            response = requests.post(
                f"{api_url}/ocr",
                files={'file': ('image.jpg', f, 'image/jpeg')},
                timeout=300  # 5 minute timeout
            )
        
        response.raise_for_status()
        result = response.json()
        
        if result['success']:
            return {
                'text': result['text'],
                'metadata': result.get('metadata', {})
            }
        else:
            raise Exception(f"OCR failed: {result.get('error')}")
            
    except requests.exceptions.Timeout:
        raise Exception("Request timed out")
    except requests.exceptions.ConnectionError:
        raise Exception("Could not connect to API")
    except Exception as e:
        raise Exception(f"Error: {str(e)}")


def example_batch_processing(image_paths: list, api_url: str = "http://localhost:5005"):
    """
    Process multiple images sequentially
    """
    results = []
    
    for i, image_path in enumerate(image_paths, 1):
        print(f"Processing {i}/{len(image_paths)}: {Path(image_path).name}")
        
        try:
            with open(image_path, 'rb') as f:
                response = requests.post(
                    f"{api_url}/ocr",
                    files={'file': f},
                    timeout=300
                )
            
            result = response.json()
            results.append({
                'image': image_path,
                'success': result['success'],
                'text': result.get('text'),
                'error': result.get('error')
            })
            
        except Exception as e:
            results.append({
                'image': image_path,
                'success': False,
                'error': str(e)
            })
    
    return results


def example_save_to_file(image_path: str, output_path: str = None, 
                         api_url: str = "http://localhost:5005"):
    """
    Process image and save output to markdown file
    """
    if output_path is None:
        output_path = Path(image_path).stem + '_ocr.md'
    
    # Get OCR result
    with open(image_path, 'rb') as f:
        response = requests.post(f"{api_url}/ocr", files={'file': f})
    
    result = response.json()
    
    if result['success']:
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result['text'])
        print(f"Saved to: {output_path}")
        return output_path
    else:
        raise Exception(result['error'])


def example_from_url(image_url: str, api_url: str = "http://localhost:5005"):
    """
    Process image from URL
    """
    # Download image
    img_response = requests.get(image_url)
    img_response.raise_for_status()
    
    # Send to OCR
    files = {'file': ('image.jpg', img_response.content, 'image/jpeg')}
    response = requests.post(f"{api_url}/ocr", files=files)
    
    result = response.json()
    if result['success']:
        return result['text']
    else:
        raise Exception(result['error'])


def example_integration_webhook(image_path: str, webhook_url: str,
                                api_url: str = "http://localhost:5005"):
    """
    Process image and send result to webhook
    """
    # Process with OCR
    with open(image_path, 'rb') as f:
        response = requests.post(f"{api_url}/ocr", files={'file': f})
    
    result = response.json()
    
    # Send to webhook
    webhook_data = {
        'source': image_path,
        'ocr_result': result['text'] if result['success'] else None,
        'success': result['success'],
        'error': result.get('error'),
        'metadata': result.get('metadata')
    }
    
    webhook_response = requests.post(webhook_url, json=webhook_data)
    return webhook_response.status_code == 200


# ============================================================================
# MAIN EXAMPLES
# ============================================================================

if __name__ == "__main__":
    API_URL = "http://localhost:5005"
    
    print("="*80)
    print("olmOCR API - Usage Examples")
    print("="*80)
    
    # Test images
    test_images = [
        r"C:\Users\alexa\OneDrive\Pictures\Samsung Gallery\Pictures\Office Lens\vettest.jpg",
        r"C:\Users\alexa\OneDrive\Pictures\grandmatest.jpg"
    ]
    
    # Example 1: Simple OCR
    print("\n1️⃣  Simple OCR Example")
    print("-" * 80)
    try:
        text = example_simple_ocr(test_images[0], API_URL)
        print(f"✅ Extracted {len(text)} characters")
        print(f"Preview: {text[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   (API might not be running. Start with: docker run --gpus all -p 5005:5005 olmocr-api)")
    
    # Example 2: With error handling
    print("\n2️⃣  With Error Handling")
    print("-" * 80)
    try:
        result = example_with_error_handling(test_images[0], API_URL)
        print(f"✅ Success!")
        print(f"   Characters: {len(result['text'])}")
        print(f"   Metadata: {result['metadata']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 3: Batch processing
    print("\n3️⃣  Batch Processing")
    print("-" * 80)
    try:
        # Only process images that exist
        existing_images = [img for img in test_images if Path(img).exists()]
        if existing_images:
            results = example_batch_processing(existing_images, API_URL)
            successful = sum(1 for r in results if r['success'])
            print(f"✅ Processed {successful}/{len(results)} images successfully")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 4: Save to file
    print("\n4️⃣  Save to File")
    print("-" * 80)
    try:
        output = example_save_to_file(test_images[0], api_url=API_URL)
        print(f"✅ Saved to: {output}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*80)
    print("Examples complete!")
    print("="*80)
    print("\n💡 Tips:")
    print("   - First request is slow (model loading)")
    print("   - Subsequent requests are fast (2-5 seconds)")
    print("   - Use batch processing for multiple images")
    print("   - Check health endpoint before processing")

