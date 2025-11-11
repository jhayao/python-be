"""
Test script for /identify/material API endpoint
Usage: python test_api.py <path_to_image.jpg>
"""

import requests
import sys
import json

def test_identify_material(image_path, backend_url="http://localhost:5001/identify/material"):
    """
    Send an image to the backend server for material identification
    
    Args:
        image_path: Path to the JPEG image file
        backend_url: URL of the backend server endpoint
    
    Returns:
        dict: JSON response from the server
    """
    try:
        # Read image file
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        print(f"Sending image to {backend_url}...")
        print(f"Image size: {len(image_data)} bytes")
        
        # Send POST request with image data
        headers = {'Content-Type': 'image/jpeg'}
        response = requests.post(backend_url, data=image_data, headers=headers, timeout=10)
        
        # Parse JSON response
        result = response.json()
        
        print("\n" + "="*50)
        print("RESPONSE:")
        print("="*50)
        print(json.dumps(result, indent=2))
        
        if result.get('success'):
            print("\n" + "="*50)
            print("IDENTIFICATION RESULT:")
            print("="*50)
            print(f"Material Type: {result['materialType']}")
            print(f"Confidence: {result['confidence'] * 100:.2f}%")
            print(f"Action: {result['action']}")
            print("\nAll Predictions:")
            for label, conf in result.get('allPredictions', {}).items():
                print(f"  {label}: {conf * 100:.2f}%")
        else:
            print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
        
        return result
        
    except FileNotFoundError:
        print(f"❌ Error: Image file not found: {image_path}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Cannot connect to backend server at {backend_url}")
        print("Make sure the backend server is running (python backend_server.py)")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <path_to_image.jpg>")
        print("\nExample:")
        print("  python test_api.py test_bottle.jpg")
        print("  python test_api.py test_can.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    test_identify_material(image_path)
