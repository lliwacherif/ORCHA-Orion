"""
Test script for OCR integration
This script tests the OCR extraction endpoint in ORCHA
"""

import requests
import base64
import json
from pathlib import Path

# Configuration
ORCHA_URL = "http://localhost:8000"
OCR_ENDPOINT = f"{ORCHA_URL}/api/v1/orcha/ocr/extract"


def encode_image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string."""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string


def test_ocr_extraction(image_path: str, mode: str = "auto", user_id: str = "test_user"):
    """
    Test OCR text extraction.
    
    Args:
        image_path: Path to image file
        mode: OCR mode (auto, fast, accurate)
        user_id: User ID for the request
    """
    print(f"\n{'='*70}")
    print(f"Testing OCR Extraction")
    print(f"{'='*70}")
    print(f"Image: {image_path}")
    print(f"Mode: {mode}")
    print(f"User ID: {user_id}")
    print(f"{'='*70}\n")
    
    # Check if file exists
    if not Path(image_path).exists():
        print(f"❌ Error: File not found: {image_path}")
        return
    
    try:
        # Encode image
        print("📷 Encoding image to base64...")
        image_data = encode_image_to_base64(image_path)
        print(f"✅ Image encoded ({len(image_data)} characters)")
        
        # Prepare request
        filename = Path(image_path).name
        payload = {
            "user_id": user_id,
            "tenant_id": "test_tenant",
            "image_data": image_data,
            "filename": filename,
            "mode": mode
        }
        
        print(f"\n🚀 Sending request to: {OCR_ENDPOINT}")
        print(f"   Filename: {filename}")
        print(f"   Mode: {mode}")
        
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
                print(f"   Confidence: {result.get('confidence', 0) * 100:.1f}%")
                print(f"   Filename: {result.get('filename')}")
                print(f"   OCR Mode: {result.get('ocr_mode')}")
                
                if result.get("metadata"):
                    metadata = result["metadata"]
                    print(f"   Total Lines: {metadata.get('total_lines', 0)}")
                    print(f"   Avg Confidence: {metadata.get('avg_confidence', 0) * 100:.1f}%")
                
                print(f"\n{'='*70}")
                
            else:
                print(f"\n❌ OCR Extraction Failed:")
                print(f"   Error: {result.get('error', 'Unknown error')}")
        else:
            print(f"\n❌ Request Failed:")
            print(f"   Status Code: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection Error:")
        print(f"   Could not connect to ORCHA at {ORCHA_URL}")
        print(f"   Make sure ORCHA is running on port 8000")
    
    except requests.exceptions.Timeout:
        print(f"\n❌ Timeout Error:")
        print(f"   Request took longer than 120 seconds")
        print(f"   Try with a smaller image or 'fast' mode")
    
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}")
        print(f"   {str(e)}")


def test_health_check():
    """Test if ORCHA is running."""
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
    """Main test function."""
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║           ORCHA OCR Integration Test Script                       ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Check if ORCHA is running
    if not test_health_check():
        print("\n⚠️  Please start ORCHA before running this test")
        return
    
    print("\n" + "="*70)
    print("Test Options:")
    print("="*70)
    print("1. Test with your own image")
    print("2. Create a test image (requires PIL)")
    print("3. Exit")
    print("="*70)
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        image_path = input("\nEnter path to your image file: ").strip()
        image_path = image_path.strip('"').strip("'")  # Remove quotes if present
        
        print("\nOCR Modes:")
        print("  auto     - Balanced speed and accuracy (recommended)")
        print("  fast     - Faster processing, lower accuracy")
        print("  accurate - Slower processing, higher accuracy")
        
        mode = input("\nEnter OCR mode (auto/fast/accurate) [auto]: ").strip().lower() or "auto"
        
        if mode not in ["auto", "fast", "accurate"]:
            print(f"⚠️  Invalid mode '{mode}', using 'auto'")
            mode = "auto"
        
        test_ocr_extraction(image_path, mode)
    
    elif choice == "2":
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            print("\n📝 Creating test image with text...")
            
            # Create a simple test image
            img = Image.new('RGB', (800, 400), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font
            try:
                font = ImageFont.truetype("arial.ttf", 32)
            except:
                font = ImageFont.load_default()
            
            # Add text to image
            text_lines = [
                "OCR Test Image",
                "This is a test document",
                "Testing PaddleOCR integration",
                "with ORCHA backend"
            ]
            
            y_position = 50
            for line in text_lines:
                draw.text((50, y_position), line, fill='black', font=font)
                y_position += 60
            
            # Save to temp file
            temp_path = "test_image_temp.png"
            img.save(temp_path)
            print(f"✅ Test image created: {temp_path}")
            
            # Test OCR
            test_ocr_extraction(temp_path, "auto")
            
            # Clean up
            import os
            os.remove(temp_path)
            print(f"\n🗑️  Cleaned up temp file")
            
        except ImportError:
            print("\n❌ PIL (Pillow) is not installed")
            print("   Install with: pip install pillow")
    
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























