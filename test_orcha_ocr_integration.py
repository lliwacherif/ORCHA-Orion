"""
Test script to verify ORCHA ↔ OCR Service integration
This script tests the connection with your actual OCR service
"""

import requests
import base64
import json
from pathlib import Path

# Configuration
ORCHA_URL = "http://localhost:8000"
OCR_SERVICE_URL = "http://localhost:8001"
OCR_ENDPOINT = f"{ORCHA_URL}/api/v1/orcha/ocr/extract"


def test_ocr_service_direct():
    """Test OCR service directly (bypassing ORCHA)"""
    print(f"\n{'='*70}")
    print(f"Testing OCR Service Directly")
    print(f"{'='*70}")
    
    # Test health check
    try:
        response = requests.get(f"{OCR_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ OCR Service is running at {OCR_SERVICE_URL}")
            print(f"   Health response: {response.json()}")
            return True
        else:
            print(f"⚠️  OCR Service responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ OCR Service is not running at {OCR_SERVICE_URL}")
        print(f"   Error: {e}")
        return False


def create_test_image():
    """Create a simple test image with text"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        print("\n📝 Creating test image...")
        
        # Create image
        img = Image.new('RGB', (600, 300), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # Add text
        text_lines = [
            "OCR Test Document",
            "This is a test for OCR integration",
            "Testing with ORCHA backend",
            "Language: English"
        ]
        
        y_position = 50
        for line in text_lines:
            draw.text((50, y_position), line, fill='black', font=font)
            y_position += 50
        
        # Save image
        test_image_path = "test_ocr_image.png"
        img.save(test_image_path)
        print(f"✅ Test image created: {test_image_path}")
        return test_image_path
        
    except ImportError:
        print("❌ PIL (Pillow) not installed. Install with: pip install pillow")
        return None
    except Exception as e:
        print(f"❌ Error creating test image: {e}")
        return None


def encode_image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string."""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string


def test_orcha_ocr_integration(image_path: str, language: str = "en"):
    """Test ORCHA OCR integration"""
    print(f"\n{'='*70}")
    print(f"Testing ORCHA OCR Integration")
    print(f"{'='*70}")
    print(f"Image: {image_path}")
    print(f"Language: {language}")
    print(f"{'='*70}\n")
    
    try:
        # Encode image
        print("📷 Encoding image to base64...")
        image_data = encode_image_to_base64(image_path)
        print(f"✅ Image encoded ({len(image_data)} characters)")
        
        # Prepare request
        filename = Path(image_path).name
        payload = {
            "user_id": "test_user",
            "tenant_id": "test_tenant",
            "image_data": image_data,
            "filename": filename,
            "language": language
        }
        
        print(f"\n🚀 Sending request to: {OCR_ENDPOINT}")
        print(f"   Filename: {filename}")
        print(f"   Language: {language}")
        
        # Send request
        response = requests.post(
            OCR_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minutes timeout
        )
        
        # Check response
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "success":
                print(f"\n{'='*70}")
                print(f"✅ OCR EXTRACTION SUCCESSFUL")
                print(f"{'='*70}")
                print(f"\n📝 Extracted Text:")
                print(f"{'-'*70}")
                print(result.get("extracted_text", ""))
                print(f"{'-'*70}")
                
                print(f"\n📊 Metadata:")
                print(f"   Lines Count: {result.get('lines_count', 0)}")
                print(f"   Filename: {result.get('filename')}")
                print(f"   Language: {result.get('language')}")
                print(f"   Message: {result.get('message')}")
                
                print(f"\n{'='*70}")
                return True
                
            else:
                print(f"\n❌ OCR Extraction Failed:")
                print(f"   Error: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"\n❌ Request Failed:")
            print(f"   Status Code: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection Error:")
        print(f"   Could not connect to ORCHA at {ORCHA_URL}")
        print(f"   Make sure ORCHA is running on port 8000")
        return False
    
    except requests.exceptions.Timeout:
        print(f"\n❌ Timeout Error:")
        print(f"   Request took longer than 120 seconds")
        return False
    
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}")
        print(f"   {str(e)}")
        return False


def test_orcha_health():
    """Test if ORCHA is running"""
    print(f"\n{'='*70}")
    print(f"Testing ORCHA Health")
    print(f"{'='*70}\n")
    
    try:
        response = requests.get(f"{ORCHA_URL}/api/v1/models", timeout=5)
        if response.status_code == 200:
            print(f"✅ ORCHA is running at {ORCHA_URL}")
            return True
        else:
            print(f"⚠️  ORCHA responded with status {response.status_code}")
            return False
    except:
        print(f"❌ ORCHA is not running at {ORCHA_URL}")
        return False


def main():
    """Main test function"""
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║           ORCHA ↔ OCR Service Integration Test                    ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Check ORCHA
    if not test_orcha_health():
        print("\n⚠️  Please start ORCHA before running this test")
        print("   Run: uvicorn app.main:app --reload --port 8000")
        return
    
    # Step 2: Check OCR Service
    if not test_ocr_service_direct():
        print("\n⚠️  Please start your OCR service before running this test")
        print("   Run: python app.py (in your OCR service directory)")
        return
    
    # Step 3: Create or use test image
    print("\n" + "="*70)
    print("Image Options:")
    print("="*70)
    print("1. Create a test image automatically")
    print("2. Use your own image")
    print("3. Exit")
    print("="*70)
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        image_path = create_test_image()
        if not image_path:
            return
        
        # Test with different languages
        languages = ["en", "fr"]
        for lang in languages:
            success = test_orcha_ocr_integration(image_path, lang)
            if success:
                print(f"\n🎉 Test successful with language: {lang}")
            else:
                print(f"\n❌ Test failed with language: {lang}")
        
        # Clean up
        import os
        os.remove(image_path)
        print(f"\n🗑️  Cleaned up test image")
    
    elif choice == "2":
        image_path = input("\nEnter path to your image file: ").strip()
        image_path = image_path.strip('"').strip("'")  # Remove quotes if present
        
        if not Path(image_path).exists():
            print(f"❌ File not found: {image_path}")
            return
        
        print("\nAvailable languages:")
        print("  en - English")
        print("  fr - French") 
        print("  ar - Arabic")
        print("  ch - Chinese")
        print("  es - Spanish")
        print("  de - German")
        print("  it - Italian")
        print("  pt - Portuguese")
        print("  ru - Russian")
        print("  ja - Japanese")
        print("  ko - Korean")
        
        language = input("\nEnter language code [en]: ").strip().lower() or "en"
        
        success = test_orcha_ocr_integration(image_path, language)
        if success:
            print(f"\n🎉 Test successful!")
        else:
            print(f"\n❌ Test failed!")
    
    elif choice == "3":
        print("\nGoodbye! 👋")
    
    else:
        print(f"\n❌ Invalid choice: {choice}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()




