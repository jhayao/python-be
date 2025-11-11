"""
Material Identification Backend API (Clean Version)
Lightweight REST API for material detection using TensorFlow Lite
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import tensorflow as tf
from PIL import Image
import io
import base64
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration
MODEL_PATH = "model/model.tflite"
LABELS_PATH = "model/labels.txt"
SAVE_IMAGES = False  # Disabled to prevent storage issues on VPS
IMAGES_SAVE_DIR = "saved_images"

# Create save directory if enabled
if SAVE_IMAGES and not os.path.exists(IMAGES_SAVE_DIR):
    os.makedirs(IMAGES_SAVE_DIR)
    print(f"Created directory: {IMAGES_SAVE_DIR}")

# Load labels
with open(LABELS_PATH, 'r') as f:
    labels = [line.strip().split(' ', 1)[1] for line in f if line.strip()]
    labels = [label for label in labels if label]

print(f"Loaded {len(labels)} labels: {labels}")

# Load TensorFlow Lite model
try:
    interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    print(f"Model loaded: {MODEL_PATH}")
    print(f"Input shape: {input_details[0]['shape']}")
except Exception as e:
    print(f"Error loading model: {e}")
    interpreter = None
    input_details = None
    output_details = None


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model_loaded": interpreter is not None,
        "labels": labels
    })


@app.route('/identify/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({
        "message": "Backend API is running",
        "model_loaded": interpreter is not None,
        "labels_available": labels
    })


@app.route('/identify/material', methods=['POST'])
def identify_material():
    """
    Identify material from image using TensorFlow Lite model
    Accepts: Binary JPEG data or Base64 encoded JSON
    """
    if interpreter is None:
        return jsonify({
            "success": False,
            "error": "Model not loaded"
        }), 500
    
    try:
        # Get image data
        content_type = request.headers.get('Content-Type', '')
        
        if 'image/jpeg' in content_type or 'image/jpg' in content_type:
            image_data = request.data
        elif 'application/json' in content_type:
            json_data = request.get_json()
            if 'image' in json_data:
                image_data = base64.b64decode(json_data['image'])
            else:
                return jsonify({
                    "success": False,
                    "error": "No image data in JSON"
                }), 400
        else:
            image_data = request.data
        
        if not image_data:
            return jsonify({
                "success": False,
                "error": "No image data received"
            }), 400
        
        # Open and process image
        image = Image.open(io.BytesIO(image_data))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Save raw image if enabled
        if SAVE_IMAGES:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            temp_filename = f"{IMAGES_SAVE_DIR}/temp_{timestamp}.jpg"
            image.save(temp_filename, 'JPEG', quality=95)
        
        # Resize for model (224x224 for Teachable Machine)
        image_resized = image.resize((224, 224))
        
        # Convert to numpy array and normalize
        image_array = np.asarray(image_resized, dtype=np.float32) / 255.0
        image_array = np.expand_dims(image_array, axis=0)
        
        # Run inference
        interpreter.set_tensor(input_details[0]['index'], image_array)
        interpreter.invoke()
        predictions = interpreter.get_tensor(output_details[0]['index'])
        
        # Get results
        confidence = float(np.max(predictions[0]))
        predicted_class_index = int(np.argmax(predictions[0]))
        
        if predicted_class_index < len(labels):
            material_type = labels[predicted_class_index]
        else:
            material_type = "Unknown"
        
        # Determine action
        if material_type == "Plastic Bottle":
            action = "sort_plastic"
        elif material_type == "Tin Can":
            action = "sort_tin_can"
        else:
            action = "reject"
        
        # Rename saved image with results
        if SAVE_IMAGES:
            confidence_percent = int(confidence * 100)
            final_filename = f"{IMAGES_SAVE_DIR}/{timestamp}_{material_type.replace(' ', '_')}_{confidence_percent}pct.jpg"
            try:
                os.rename(temp_filename, final_filename)
                print(f"Saved: {final_filename}")
            except Exception as e:
                print(f"Error saving image: {e}")
        
        print(f"Detection: {material_type} ({confidence:.2%})")
        
        return jsonify({
            "success": True,
            "materialType": material_type,
            "confidence": round(confidence, 2),
            "action": action,
            "allPredictions": {
                labels[i]: float(predictions[0][i]) 
                for i in range(len(labels))
            }
        })
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    print("="*60)
    print("Material Identification API Server")
    print("="*60)
    print(f"Model: {MODEL_PATH}")
    print(f"Labels: {LABELS_PATH}")
    print(f"Image Saving: {'ENABLED' if SAVE_IMAGES else 'DISABLED'}")
    if SAVE_IMAGES:
        print(f"Save Directory: {IMAGES_SAVE_DIR}/")
    print("\n" + "="*60)
    print("API Endpoints:")
    print("="*60)
    print("  GET  /health              - Health check")
    print("  GET  /identify/test       - Test endpoint")
    print("  POST /identify/material   - Detect material from image")
    print("="*60)
    print("\nServer running at: http://localhost:5001")
    print("Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    # Production deployment: use gunicorn
    # gunicorn -w 2 -b 0.0.0.0:5001 --timeout 120 backend_api:app
    
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False, threaded=True)
