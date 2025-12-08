"""
Test script for the refactored Auto-Fill API v2 (Dynamic Field Extraction)

This script demonstrates how to use the new dynamic auto-fill endpoint.

Usage:
    python test_auto_fill_v2.py <file_path>

Example:
    python test_auto_fill_v2.py sample_id_card.pdf
"""

import requests
import json
import sys
import os
from pathlib import Path

# Configuration
API_URL = "http://localhost:8000/api/v1/orcha/auto-fill"

def test_auto_fill(file_path: str, fields: list):
    """
    Test the auto-fill endpoint with a document and field list.
    
    Args:
        file_path: Path to the document file
        fields: List of field definitions
    
    Returns:
        API response as dict
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found: {file_path}")
        return None
    
    # Detect content type
    ext = Path(file_path).suffix.lower()
    content_type_map = {
        '.pdf': 'application/pdf',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg'
    }
    content_type = content_type_map.get(ext, 'application/octet-stream')
    
    print(f"\n{'='*60}")
    print(f"🔍 Testing Auto-Fill API v2")
    print(f"{'='*60}")
    print(f"📄 File: {file_path}")
    print(f"📋 Content Type: {content_type}")
    print(f"🎯 Requested Fields: {', '.join([f['field_name'] for f in fields])}")
    print(f"{'='*60}\n")
    
    try:
        # Prepare request
        with open(file_path, 'rb') as f:
            files = {
                'file': (os.path.basename(file_path), f, content_type)
            }
            data = {
                'fields': json.dumps(fields)
            }
            
            # Send request
            print("⏳ Sending request to API...")
            response = requests.put(API_URL, files=files, data=data, timeout=60)
            
            # Parse response
            result = response.json()
            
            print(f"✅ Response received (Status: {response.status_code})\n")
            
            # Display result
            print(f"{'='*60}")
            print(f"📊 RESULT")
            print(f"{'='*60}")
            print(f"Success: {result.get('success')}")
            print(f"Message: {result.get('message')}")
            print(f"\nExtracted Data:")
            print(json.dumps(result.get('data', {}), indent=2))
            print(f"{'='*60}\n")
            
            # Interpretation
            if result.get('success'):
                if result.get('message') == 'success':
                    print("✅ SUCCESS: Data extracted successfully!")
                    
                    # Check which fields were found
                    data = result.get('data', {})
                    found_fields = [k for k, v in data.items() if v is not None and v != ""]
                    missing_fields = [k for k, v in data.items() if v is None or v == ""]
                    
                    if found_fields:
                        print(f"✅ Found fields: {', '.join(found_fields)}")
                    if missing_fields:
                        print(f"⚠️  Missing fields: {', '.join(missing_fields)}")
                        
                elif result.get('message') == 'invalid doc':
                    print("⚠️  INVALID DOCUMENT: The document is unreadable or contains no text")
                else:
                    print(f"ℹ️  INFO: {result.get('message')}")
            else:
                print(f"❌ ERROR: {result.get('message')}")
            
            return result
            
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: Could not connect to API at {API_URL}")
        print("   Make sure the ORCHA server is running.")
        return None
    except requests.exceptions.Timeout:
        print(f"❌ ERROR: Request timed out")
        return None
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def run_test_suite():
    """Run a comprehensive test suite with different field configurations."""
    
    # Check if file argument provided
    if len(sys.argv) < 2:
        print("❌ Error: Please provide a file path")
        print("\nUsage:")
        print("  python test_auto_fill_v2.py <file_path>")
        print("\nExample:")
        print("  python test_auto_fill_v2.py sample_document.pdf")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Test 1: Basic Identity Fields (like old API)
    print("\n" + "="*60)
    print("TEST 1: Basic Identity Fields (Compatible with v1)")
    print("="*60)
    fields_basic = [
        {"field_name": "firstname", "field_type": "string"},
        {"field_name": "lastname", "field_type": "string"},
        {"field_name": "birth_date", "field_type": "date"},
        {"field_name": "gender", "field_type": "string"}
    ]
    test_auto_fill(file_path, fields_basic)
    
    input("\nPress Enter to continue to Test 2...")
    
    # Test 2: Extended Identity Fields
    print("\n" + "="*60)
    print("TEST 2: Extended Identity Fields")
    print("="*60)
    fields_extended = [
        {"field_name": "firstname", "field_type": "string"},
        {"field_name": "lastname", "field_type": "string"},
        {"field_name": "birth_date", "field_type": "date"},
        {"field_name": "birth_place", "field_type": "string"},
        {"field_name": "nationality", "field_type": "string"},
        {"field_name": "document_number", "field_type": "string"},
        {"field_name": "expiry_date", "field_type": "date"},
        {"field_name": "address", "field_type": "string"}
    ]
    test_auto_fill(file_path, fields_extended)
    
    input("\nPress Enter to continue to Test 3...")
    
    # Test 3: Custom Fields
    print("\n" + "="*60)
    print("TEST 3: Custom Fields (Flexible)")
    print("="*60)
    fields_custom = [
        {"field_name": "full_name", "field_type": "string"},
        {"field_name": "date_of_birth", "field_type": "date"},
        {"field_name": "id_number", "field_type": "string"},
        {"field_name": "issuing_authority", "field_type": "string"}
    ]
    test_auto_fill(file_path, fields_custom)
    
    print("\n" + "="*60)
    print("✅ Test suite completed!")
    print("="*60)

def quick_test():
    """Quick test with command line file."""
    if len(sys.argv) < 2:
        print("❌ Error: Please provide a file path")
        print("\nUsage:")
        print("  python test_auto_fill_v2.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Default fields for quick test
    fields = [
        {"field_name": "firstname", "field_type": "string"},
        {"field_name": "lastname", "field_type": "string"},
        {"field_name": "birth_date", "field_type": "date"},
        {"field_name": "nationality", "field_type": "string"}
    ]
    
    test_auto_fill(file_path, fields)

if __name__ == "__main__":
    # Uncomment one of these:
    
    # Option 1: Run full test suite with multiple configurations
    # run_test_suite()
    
    # Option 2: Quick single test
    quick_test()



