"""
Convert an image to base64 encoding for use in Postman JSON requests
Usage: python encode_image_base64.py <image_path>
"""

import base64
import sys

def encode_image_to_base64(image_path):
    """Convert image file to base64 string"""
    try:
        with open(image_path, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
        print("\n" + "="*80)
        print("BASE64 ENCODED IMAGE")
        print("="*80)
        print("\nCopy this entire string and paste into Postman JSON body:")
        print("\n{")
        print('  "image": "' + encoded_string + '"')
        print("}")
        print("\n" + "="*80)
        print(f"Length: {len(encoded_string)} characters")
        print("="*80)
        
        # Also save to file for easy copying
        output_file = "base64_image.txt"
        with open(output_file, 'w') as f:
            f.write(encoded_string)
        print(f"\n✓ Base64 string also saved to: {output_file}")
        
        return encoded_string
        
    except FileNotFoundError:
        print(f"❌ Error: Image file not found: {image_path}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python encode_image_base64.py <image_path>")
        print("\nExample:")
        print("  python encode_image_base64.py test_bottle.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    encode_image_to_base64(image_path)
