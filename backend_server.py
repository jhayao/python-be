"""
Material Identification Backend Server
Uses Teachable Machine TensorFlow Lite model for classification
With OpenCV real-time monitoring from ESP32-CAM stream
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import numpy as np
import tensorflow as tf
from PIL import Image
import io
import base64
import cv2
import threading
import urllib.request
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for ESP8266/ESP32-CAM requests

# Load the Teachable Machine TensorFlow Lite model
MODEL_PATH = "model/model.tflite"
LABELS_PATH = "model/labels.txt"

# Image saving configuration
SAVE_IMAGES = True  # Set to False to disable saving images
IMAGES_SAVE_DIR = "saved_images"  # Directory to save images

# Create save directory if it doesn't exist
if SAVE_IMAGES and not os.path.exists(IMAGES_SAVE_DIR):
    os.makedirs(IMAGES_SAVE_DIR)
    print(f"Created directory for saving images: {IMAGES_SAVE_DIR}")

# ESP32-CAM Streaming URL (update with your ESP32-CAM IP)
ESP32_CAM_STREAM_URL = "http://192.168.31.76:81/stream"  # Port 81 for ESP32-CAM stream

# Global variables for real-time monitoring
latest_prediction = {
    "materialType": "None",
    "confidence": 0.0,
    "allPredictions": {},
    "frame_count": 0
}
prediction_lock = threading.Lock()
monitoring_active = False

# Load labels
with open(LABELS_PATH, 'r') as f:
    labels = [line.strip().split(' ', 1)[1] for line in f if line.strip()]
    # Remove empty lines
    labels = [label for label in labels if label]

print(f"Loaded {len(labels)} labels: {labels}")

# Load TensorFlow Lite model
try:
    interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
    
    # Get input and output tensors
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    print(f"TensorFlow Lite model loaded successfully from {MODEL_PATH}")
    print(f"Input shape: {input_details[0]['shape']}")
    print(f"Output shape: {output_details[0]['shape']}")
    print(f"Input dtype: {input_details[0]['dtype']}")
    print(f"Output dtype: {output_details[0]['dtype']}")
    
except Exception as e:
    print(f"Error loading TensorFlow Lite model: {e}")
    import traceback
    traceback.print_exc()
    interpreter = None
    input_details = None
    output_details = None

def process_frame(frame):
    """Process a single frame through the TensorFlow Lite model and return predictions"""
    if interpreter is None:
        # Return a placeholder prediction if model isn't loaded
        return {
            "materialType": "Model Not Loaded",
            "confidence": 0.0,
            "allPredictions": {"Plastic Bottle": 0.0, "Tin Can": 0.0, "Other": 0.0},
            "predictedIndex": -1
        }
    
    try:
        # Resize frame to model input size (224x224)
        resized = cv2.resize(frame, (224, 224))
        
        # Convert BGR to RGB (OpenCV uses BGR, model expects RGB)
        rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # Convert to numpy array and normalize
        image_array = np.asarray(rgb_frame, dtype=np.float32) / 255.0
        
        # Add batch dimension
        image_array = np.expand_dims(image_array, axis=0)
        
        # Set input tensor
        interpreter.set_tensor(input_details[0]['index'], image_array)
        
        # Run inference
        interpreter.invoke()
        
        # Get output tensor
        predictions = interpreter.get_tensor(output_details[0]['index'])
        
        # Get the highest confidence prediction
        confidence = float(np.max(predictions[0]))
        predicted_class_index = int(np.argmax(predictions[0]))
        
        # Get material type
        if predicted_class_index < len(labels):
            material_type = labels[predicted_class_index]
        else:
            material_type = "Unknown"
        
        # Get all predictions
        all_predictions = {
            labels[i]: float(predictions[0][i]) 
            for i in range(len(labels))
        }
        
        return {
            "materialType": material_type,
            "confidence": confidence,
            "allPredictions": all_predictions,
            "predictedIndex": predicted_class_index
        }
    except Exception as e:
        print(f"Error processing frame: {e}")
        import traceback
        traceback.print_exc()
        return None

def draw_predictions(frame, prediction):
    """Draw prediction information on the frame"""
    if prediction is None:
        return frame
    
    material_type = prediction["materialType"]
    confidence = prediction["confidence"]
    all_predictions = prediction["allPredictions"]
    
    # Draw main prediction
    text = f"{material_type}: {confidence:.2%}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    thickness = 2
    
    # Get text size for positioning
    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    
    # Background rectangle for main prediction
    cv2.rectangle(frame, (10, 10), (text_width + 20, text_height + 30), (0, 0, 0), -1)
    
    # Choose color based on material type
    if material_type == "Plastic Bottle":
        color = (0, 255, 0)  # Green
    elif material_type == "Tin Can":
        color = (255, 165, 0)  # Orange
    elif material_type == "Model Not Loaded":
        color = (0, 255, 255)  # Yellow/Cyan for warning
    else:
        color = (0, 0, 255)  # Red
    
    # Draw main prediction text
    cv2.putText(frame, text, (15, text_height + 15), font, font_scale, color, thickness)
    
    # Draw all predictions
    y_offset = text_height + 50
    for i, (label, conf) in enumerate(all_predictions.items()):
        pred_text = f"{label}: {conf:.2%}"
        # Background for each prediction
        (pred_width, pred_height), _ = cv2.getTextSize(pred_text, font, 0.6, 1)
        cv2.rectangle(frame, (10, y_offset - 15), (pred_width + 15, y_offset + 5), (0, 0, 0), -1)
        cv2.putText(frame, pred_text, (12, y_offset), font, 0.6, (255, 255, 255), 1)
        y_offset += 25
    
    # Draw frame counter
    with prediction_lock:
        frame_count = latest_prediction.get("frame_count", 0)
    cv2.putText(frame, f"Frames: {frame_count}", (10, frame.shape[0] - 10), 
                font, 0.5, (255, 255, 255), 1)
    
    return frame

def monitor_stream():
    """Monitor ESP32-CAM stream and process frames in real-time with OpenCV display"""
    global latest_prediction, monitoring_active
    
    monitoring_active = True
    print(f"Starting stream monitoring from {ESP32_CAM_STREAM_URL}")
    print("Displaying live feed in OpenCV window...")
    print("Press 'q' in the window to stop monitoring")
    
    # Create OpenCV window
    window_name = "ESP32-CAM Real-Time Monitoring (Press 'q' to quit)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)  # Resize window
    
    cap = None
    frame_skip = 5  # Process every 5th frame to reduce load
    frame_counter = 0
    last_frame_time = time.time()  # Track when last frame was received
    
    # Setup requests session for better stream handling (for future use)
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=0.1)
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    while monitoring_active:
        try:
            if cap is None or not cap.isOpened():
                print(f"Connecting to ESP32-CAM stream at {ESP32_CAM_STREAM_URL}...")
                cap = cv2.VideoCapture(ESP32_CAM_STREAM_URL)
                
                # Set buffer size to reduce latency
                try:
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    # These properties might not be supported on all backends
                    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)  # 5 second timeout
                    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)  # 5 second timeout
                except:
                    pass  # Some backends don't support these properties
                
                if not cap.isOpened():
                    print(f"Failed to connect to stream. Retrying in 3 seconds...")
                    # Show waiting message in window
                    waiting_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(waiting_frame, "Connecting to ESP32-CAM...", 
                               (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                    cv2.putText(waiting_frame, f"URL: {ESP32_CAM_STREAM_URL}", 
                               (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                    cv2.imshow(window_name, waiting_frame)
                    
                    # Check for 'q' key while waiting
                    key = cv2.waitKey(100) & 0xFF
                    if key == ord('q'):
                        monitoring_active = False
                        break
                    
                    time.sleep(3)
                    continue
            
            # Try to read frame with timeout handling
            ret = False
            frame = None
            
            # Check if we've been waiting too long (timeout detection)
            time_since_last_frame = time.time() - last_frame_time
            if time_since_last_frame > 10:  # 10 seconds without frames = timeout
                print("Stream timeout detected. Reconnecting...")
                cap.release()
                cap = None
                continue
            
            # Try reading frame (non-blocking if possible)
            ret, frame = cap.read()
            
            # If read succeeds, update timestamp
            if ret and frame is not None:
                last_frame_time = time.time()
            
            # If read fails, check if stream is still open
            if not ret or frame is None:
                # Check if stream is actually open
                if not cap.isOpened():
                    print("Stream closed. Reconnecting...")
                    cap.release()
                    cap = None
                    continue
                else:
                    # Frame read failed but stream is open - might be temporary
                    # Show last frame or error message but don't wait too long
                    if "frame" in latest_prediction:
                        # Show last successful frame
                        frame_with_overlay = latest_prediction.get("frame")
                        if frame_with_overlay is not None:
                            cv2.putText(frame_with_overlay, "Stream paused...", 
                                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                            cv2.imshow(window_name, frame_with_overlay)
                    else:
                        # Show error message
                        error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                        cv2.putText(error_frame, "Reading frame...", 
                                   (200, 230), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                        cv2.putText(error_frame, "Press 'q' to quit", 
                                   (200, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
                        cv2.imshow(window_name, error_frame)
                    
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        monitoring_active = False
                        break
                    
                    # Don't wait long - try reading again quickly
                    time.sleep(0.1)
                    continue
            
            frame_counter += 1
            
            # Process every Nth frame (only if model is loaded)
            if interpreter is not None and frame_counter % frame_skip == 0:
                prediction = process_frame(frame)
                
                if prediction and prediction.get("materialType") != "Model Not Loaded":
                    with prediction_lock:
                        latest_prediction = {
                            "materialType": prediction["materialType"],
                            "confidence": prediction["confidence"],
                            "allPredictions": prediction["allPredictions"],
                            "frame_count": frame_counter
                        }
            
            # Draw predictions on frame
            with prediction_lock:
                current_pred = latest_prediction.copy()
            
            # Always draw overlay (will show "Model Not Loaded" if model isn't available)
            frame_with_overlay = draw_predictions(frame.copy(), current_pred if current_pred.get("materialType") != "None" else None)
            
            # Store latest frame for web streaming
            with prediction_lock:
                latest_prediction["frame"] = frame_with_overlay
            
            # Display frame in OpenCV window (non-blocking)
            cv2.imshow(window_name, frame_with_overlay)
            
            # Check for 'q' key press to quit (non-blocking wait)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n'q' pressed - Stopping monitoring...")
                monitoring_active = False
                break
            
            # Small delay to prevent excessive CPU usage
            time.sleep(0.01)  # ~100 FPS max
            
        except KeyboardInterrupt:
            print("\nInterrupted by user")
            monitoring_active = False
            break
        except Exception as e:
            print(f"Error in stream monitoring: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error in window
            error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(error_frame, "Error occurred", 
                       (200, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(error_frame, "Check console for details", 
                       (150, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            cv2.imshow(window_name, error_frame)
            cv2.waitKey(100)
            
            time.sleep(2)
            if cap is not None:
                cap.release()
                cap = None
    
    # Cleanup
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    print("Stream monitoring stopped")

def generate_frames():
    """Generate frames for web streaming with overlay"""
    while True:
        try:
            with prediction_lock:
                if "frame" in latest_prediction:
                    frame = latest_prediction["frame"].copy()
                else:
                    # Create a placeholder frame if no stream available
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(frame, "Waiting for ESP32-CAM stream...", 
                               (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    cv2.putText(frame, f"Stream URL: {ESP32_CAM_STREAM_URL}", 
                               (50, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.033)  # ~30 FPS
            
        except Exception as e:
            print(f"Error generating frame: {e}")
            time.sleep(1)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model_loaded": interpreter is not None,
        "labels": labels,
        "stream_url": ESP32_CAM_STREAM_URL,
        "monitoring_active": monitoring_active
    })

@app.route('/video_feed')
def video_feed():
    """Video streaming route with real-time predictions"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/prediction')
def get_prediction():
    """Get latest prediction results"""
    with prediction_lock:
        pred = latest_prediction.copy()
        if "frame" in pred:
            del pred["frame"]  # Remove frame data from JSON response
    return jsonify(pred)

@app.route('/bin/update', methods=['POST'])
def bin_update():
    """Receive bin level updates (optional - for future use)"""
    try:
        data = request.get_json()
        if data:
            print(f"Bin update received: {data}")
            # You can store this data, log it, or process it as needed
            # For now, just acknowledge receipt
            return jsonify({
                "success": True,
                "message": "Bin update received"
            })
        else:
            return jsonify({
                "success": False,
                "error": "No data received"
            }), 400
    except Exception as e:
        print(f"Error processing bin update: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/identify/material', methods=['POST'])
def identify_material():
    """
    Identify material from image using TensorFlow Lite model
    Accepts JPEG image binary data or base64 encoded image
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
            # Binary JPEG data
            image_data = request.data
        elif 'application/json' in content_type:
            # Base64 encoded image
            json_data = request.get_json()
            if 'image' in json_data:
                image_data = base64.b64decode(json_data['image'])
            else:
                return jsonify({
                    "success": False,
                    "error": "No image data in JSON"
                }), 400
        else:
            # Try to read as binary
            image_data = request.data
        
        if not image_data:
            return jsonify({
                "success": False,
                "error": "No image data received"
            }), 400
        
        # Process image
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Save raw image before processing
        if SAVE_IMAGES:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            temp_filename = f"{IMAGES_SAVE_DIR}/temp_{timestamp}.jpg"
            image.save(temp_filename, 'JPEG', quality=95)
        
        # Resize to model input size (Teachable Machine default is 224x224)
        image = image.resize((224, 224))
        
        # Convert to numpy array and normalize
        image_array = np.asarray(image, dtype=np.float32) / 255.0
        
        # Add batch dimension
        image_array = np.expand_dims(image_array, axis=0)
        
        # Set input tensor
        interpreter.set_tensor(input_details[0]['index'], image_array)
        
        # Run inference
        interpreter.invoke()
        
        # Get output tensor
        predictions = interpreter.get_tensor(output_details[0]['index'])
        
        # Get the highest confidence prediction
        confidence = float(np.max(predictions[0]))
        predicted_class_index = int(np.argmax(predictions[0]))
        
        # Get material type
        if predicted_class_index < len(labels):
            material_type = labels[predicted_class_index]
        else:
            material_type = "Unknown"
        
        # Determine action based on material type
        action = None
        if material_type == "Plastic Bottle":
            action = "sort_plastic"
        elif material_type == "Tin Can":
            action = "sort_tin_can"
        else:  # Other or Unknown
            action = "reject"
        
        # Rename saved image with material type and confidence
        if SAVE_IMAGES:
            confidence_percent = int(confidence * 100)
            final_filename = f"{IMAGES_SAVE_DIR}/{timestamp}_{material_type.replace(' ', '_')}_{confidence_percent}pct.jpg"
            try:
                os.rename(temp_filename, final_filename)
                print(f"Saved image: {final_filename}")
            except Exception as e:
                print(f"Error renaming image: {e}")
        
        print(f"Prediction: {material_type} (confidence: {confidence:.2f}, index: {predicted_class_index})")
        
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
        print(f"Error processing image: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/identify/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({
        "message": "Backend server is running",
        "model_loaded": interpreter is not None,
        "labels_available": labels,
        "stream_url": ESP32_CAM_STREAM_URL
    })

@app.route('/')
def index():
    """Simple HTML page to view the stream"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ESP32-CAM Stream with AI Predictions</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                background-color: #1a1a1a;
                color: white;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            img {
                max-width: 100%;
                border: 2px solid #00ff00;
                border-radius: 10px;
            }
            .info {
                margin-top: 20px;
                padding: 10px;
                background-color: #2a2a2a;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ESP32-CAM Real-Time Monitoring</h1>
            <img src="/video_feed" alt="Video Feed">
            <div class="info">
                <p>Stream URL: <code>""" + ESP32_CAM_STREAM_URL + """</code></p>
                <p>Latest Prediction: <span id="prediction">Loading...</span></p>
                <p>Confidence: <span id="confidence">-</span></p>
            </div>
        </div>
        <script>
            setInterval(async () => {
                try {
                    const response = await fetch('/prediction');
                    const data = await response.json();
                    document.getElementById('prediction').textContent = data.materialType || 'None';
                    document.getElementById('confidence').textContent = 
                        data.confidence ? (data.confidence * 100).toFixed(2) + '%' : '-';
                } catch (e) {
                    console.error('Error fetching prediction:', e);
                }
            }, 1000);
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("Starting Material Identification Backend Server...")
    print("Model path:", MODEL_PATH)
    print("Labels path:", LABELS_PATH)
    if SAVE_IMAGES:
        print(f"Image saving: ENABLED (Directory: {IMAGES_SAVE_DIR}/)")
    else:
        print("Image saving: DISABLED")
    print("\nAPI Server running at: http://localhost:5001")
    print("API endpoints:")
    print("  - GET  /health - Health check")
    print("  - GET  /identify/test - Test endpoint")
    print("  - POST /identify/material - Identify material from image")
    
    # For production VPS deployment, consider using gunicorn instead:
    # gunicorn -w 2 -b 0.0.0.0:5001 --timeout 120 backend_server:app
    
    # Run Flask app on port 5001 (port 5000 is often reserved on Windows)
    # use_reloader=False prevents timer overflow warnings
    # For VPS: Set threaded=True for better concurrency on single CPU
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False, threaded=True)
