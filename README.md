# ESP32-CAM Recycling Machine with AI Material Identification

This project implements an IoT recycling machine using ESP32-CAM for camera capture and material identification. The system uses a Teachable Machine TensorFlow Lite model for real-time material classification.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Hardware Components](#hardware-components)
3. [Power Supply](#power-supply)
4. [Software Setup](#software-setup)
5. [Arduino IDE Setup](#arduino-ide-setup)
6. [ESP32-CAM Configuration](#esp32-cam-configuration)
7. [Backend Server Setup](#backend-server-setup)
8. [System Workflow](#system-workflow)
9. [Web Interface](#web-interface)
10. [Real-Time Streaming](#real-time-streaming)
11. [API Endpoints](#api-endpoints)
12. [Troubleshooting](#troubleshooting)
13. [File Structure](#file-structure)

---

## System Architecture

- **ESP32-CAM**: Standalone controller with built-in web server
  - Live video streaming on port 81
  - Web interface to trigger material identification
  - Direct communication with backend server for AI classification
- **Backend Server** (Python/Flask): Runs on your laptop
  - TensorFlow Lite model inference
  - Real-time monitoring with OpenCV
  - REST API for material identification

---

## Hardware Components

- **ESP32-CAM** (AI Thinker)
- **Power Supply**: 5V 2A USB power adapter (or use USB port for programming)
- **USB-to-Serial Adapter**: Required for uploading code (FTDI, CP2102, or CH340)
- **Optional Components** (for future expansion):
  - IR Sensor (for automatic detection)
  - Servos (for automated sorting)
  - Ultrasonic Sensors (for bin level monitoring)

---

## Power Supply

ESP32-CAM requires **5V power supply**:
- **Option 1**: USB power adapter (5V 2A minimum)
- **Option 2**: Use USB port during development (also used for programming)

**Power Requirements:**
- Normal operation: ~200-500mA @ 5V
- Peak (WiFi + Camera streaming): ~500-1000mA @ 5V
- Use a 5V 2A adapter for stable operation

---

## Software Setup

### Prerequisites

- **Arduino IDE** (1.8.x or 2.x)
- **Python 3.11 or 3.12** (recommended for TensorFlow compatibility)
- **USB-to-Serial adapter** drivers installed (CH340/FTDI/CP2102)

---

## Arduino IDE Setup

### Step 1: Add ESP32 Board Manager URL

1. Open **Arduino IDE**
2. Go to **File → Preferences** (or **Arduino → Preferences** on Mac)
3. In **"Additional Boards Manager URLs"**, add:
   ```
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```
   (If you have other URLs, separate them with commas)
4. Click **OK**

### Step 2: Install ESP32 Board Support

1. Go to **Tools → Board → Boards Manager...**
2. Search for: **esp32**
3. Install **"esp32 by Espressif Systems"**
4. Wait for installation to complete (this may take several minutes)

### Step 3: Select ESP32-CAM Board

1. Go to **Tools → Board → esp32**
2. Select **"AI Thinker ESP32-CAM"**

### Step 4: Configure ESP32-CAM Settings

**Important settings:**
- **Partition Scheme**: Default 4MB with spiffs (or "Huge APP")
- **PSRAM**: Enabled
- **Flash Size**: 4MB (3MB APP/1MB SPIFFS) or as available
- **Upload Speed**: 115200 (can lower to 921600 if you have issues)
- **Port**: Select your COM port (where ESP32-CAM is connected)

### Required Libraries

**For ESP32-CAM:**
- **ArduinoJson** (via Library Manager)
- WebServer library (comes with board support)
- ESP32 libraries (come with board support)
- HTTPClient library (comes with board support)

**Install Libraries:**
1. Go to **Sketch → Include Library → Manage Libraries**
2. Search for **ArduinoJson**
3. Install **ArduinoJson by Benoit Blanchon** (version 6.x or 7.x)

### Uploading Code to ESP32-CAM

**Important Notes:**
- **ESP32-CAM doesn't have built-in USB-to-Serial**: You need a USB-to-Serial adapter (FTDI or CP2102)
- **GPIO 0 must be LOW during boot** to enter upload mode
- Many ESP32-CAM boards have an **IO0 button** - hold it down while pressing/resetting

**Upload Steps:**
1. Connect ESP32-CAM to USB-to-Serial adapter:
   - **5V** → ESP32-CAM 5V
   - **GND** → ESP32-CAM GND
   - **TX** → ESP32-CAM U0R (GPIO 3)
   - **RX** → ESP32-CAM U0T (GPIO 1)
2. Select correct **COM port** in Arduino IDE
3. **Hold IO0 button** (if available) or connect GPIO 0 to GND
4. Press **Reset button** (while holding IO0)
5. Release IO0 button
6. Click **Upload** in Arduino IDE
7. Wait for upload to complete

**Alternative: Using USB Programmer Module**
Some ESP32-CAM boards come with a USB programming module. Follow the module's instructions.

### USB-to-Serial Driver Installation

Your USB-to-Serial adapter may need drivers:

**CH340 Driver:**
- **Windows**: Download from https://sparks.gogo.co.nz/ch340.html
- **Mac**: Usually works automatically
- **Linux**: Usually works automatically

**FTDI Driver:**
- Download from: https://ftdichip.com/drivers/

**CP2102 Driver:**
- Download from: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers

---

## ESP32-CAM Configuration

### Upload Code

1. Open `esp32_cam_controller/esp32_cam_controller.ino` in Arduino IDE
2. Configure WiFi credentials:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   const char* IDENTIFICATION_BACKEND_URL = "http://YOUR_LAPTOP_IP:5000/identify/material";
   ```
3. Upload to ESP32-CAM (follow Arduino IDE Setup steps above)

### After Upload

1. Open Serial Monitor (115200 baud)
2. Press Reset button on ESP32-CAM
3. You should see initialization messages:
   ```
   ESP32-CAM Recycling Machine Controller
   Standalone Mode - Direct Backend Integration
   Camera initialized successfully
   Connecting to WiFi: YOUR_WIFI_SSID
   ...
   WiFi connected!
   IP address: 192.168.x.x
   Stream available at: http://192.168.x.x:81/stream
   Trigger identification: http://192.168.x.x:81/capture
   ```
4. **Note the IP address** - you'll need it for backend server configuration

---

## Backend Server Setup

### Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- TensorFlow (>=2.15.0)
- Flask
- OpenCV (>=4.8.1)
- NumPy
- Pillow
- Requests

### Configure Backend

1. Ensure `model/model.tflite` and `model/labels.txt` are in place
2. Update `ESP32_CAM_STREAM_URL` in `backend_server.py` with your ESP32-CAM IP address:
   ```python
   ESP32_CAM_STREAM_URL = "http://192.168.x.x:81/stream"  # Use your ESP32-CAM IP
   ```

### Run Backend Server

```bash
python backend_server.py
```

The server will:
- Start on `http://0.0.0.0:5000` (accessible on your network)
- Open an OpenCV window showing real-time video stream with AI predictions
- Provide REST API at `/identify/material` for image classification

You should see:
```
Starting Material Identification Backend Server...
Stream monitoring started in background thread
Access the monitoring interface at: http://localhost:5000/
```

---

## System Workflow

### 1. Initialization

- ESP32-CAM connects to WiFi
- Camera initializes
- Web server starts on port 81
- Backend server connects to ESP32-CAM stream

### 2. Material Identification

- User clicks "🔍 Identify Material" button on web interface (http://ESP32_CAM_IP:81)
- ESP32-CAM captures image
- Image sent to backend server
- Backend processes image through TensorFlow Lite model
- Model returns: "Plastic Bottle", "Tin Can", or "Other"
- Result displayed on web interface

### 3. Real-Time Monitoring

- Backend server connects to ESP32-CAM stream (http://ESP32_CAM_IP:81/stream)
- OpenCV window displays live video with AI predictions overlaid
- Predictions update automatically as frames are processed
- Press 'q' in OpenCV window to quit monitoring

---

## Web Interface

### ESP32-CAM Web Interface

Access at: `http://ESP32_CAM_IP:81`

**Endpoints:**
- `/` - Main web interface with video stream and identification button
- `/stream` - MJPEG video stream
- `/capture` - Trigger material identification (GET request, returns JSON)
- `/result` - Get last identification result (JSON)
- `/status` - System status (JSON)

### Backend Web Interface

Access at: `http://localhost:5000/` or `http://YOUR_LAPTOP_IP:5000/`

**Features:**
- Video feed with predictions overlay
- Latest prediction data display
- System health status

---

## Real-Time Streaming

### Overview

The system supports real-time video streaming from ESP32-CAM with live AI predictions displayed directly on your laptop via OpenCV window (no browser needed).

### Architecture

```
ESP32-CAM → Streaming Server (Port 81)
         ↓
         └─→ Backend Server (Port 5000) → OpenCV Processing → Direct Display
```

### Setup

1. **Update ESP32-CAM IP Address**
   - After uploading ESP32-CAM code, check Serial Monitor for IP address
   - Example: `IP address: 192.168.123.45`

2. **Update Backend Server Configuration**
   - Edit `backend_server.py`:
   ```python
   ESP32_CAM_STREAM_URL = "http://192.168.123.45:81/stream"  # Use your ESP32-CAM IP
   ```

3. **Run Backend Server**
   ```bash
   python backend_server.py
   ```
   - OpenCV window will open automatically showing live stream with predictions

### Features

**Real-Time Video Stream:**
- Live video feed from ESP32-CAM
- Frames processed by AI model in real-time
- Confidence scores displayed on video

**Overlay Information:**
- **Main Prediction**: Top prediction with color coding
  - Green = Plastic Bottle
  - Orange = Tin Can
  - Red = Other/Rejected
- **All Predictions**: Confidence scores for all classes
- **Frame Counter**: Total frames processed
- **Model Status**: Shows if model is loaded

### Performance

**Frame Processing:**
- **Stream Rate**: ~30 FPS from ESP32-CAM
- **Processing Rate**: Every 5th frame processed (adjustable in code)
- **Reason**: AI model processing is CPU-intensive, processing every frame would lag

**Adjusting Processing Rate:**

In `backend_server.py`, modify:
```python
frame_skip = 5  # Process every 5th frame
```

- Lower number = more frequent predictions (more CPU)
- Higher number = less frequent predictions (less CPU)

### Integration with Material Identification

The streaming works in parallel with manual material identification:
- User triggers identification via ESP32-CAM web interface (`/capture` endpoint)
- ESP32-CAM captures image → Sends to backend
- Backend processes → Returns result
- **In parallel**: Backend also continuously streams and processes video for real-time monitoring

Both manual identification and real-time streaming work together!

---

## API Endpoints

### Backend Server Endpoints

- `GET /health` - Health check and system status
- `GET /video_feed` - Video stream with predictions (web interface)
- `GET /prediction` - Latest prediction data (JSON)
- `POST /identify/material` - Identify material from image (JPEG binary or base64)
- `POST /bin/update` - Bin level updates (optional, for future use)

### ESP32-CAM Endpoints

- `http://ESP32_IP:81/stream` - MJPEG video stream
- `http://ESP32_IP:81/` - Web interface for ESP32-CAM
- `http://ESP32_IP:81/capture` - Trigger material identification
- `http://ESP32_IP:81/result` - Get last identification result
- `http://ESP32_IP:81/status` - JSON status: IP, RSSI, connection status

---

## Model Information

The TensorFlow Lite model (`model/model.tflite`) classifies materials into:
- **Plastic Bottle** → Action: `sort_plastic`
- **Tin Can** → Action: `sort_tin_can`
- **Other** → Action: `reject`

Labels are defined in `model/labels.txt`.

---

## Troubleshooting

### Arduino IDE Issues

**Can't find Boards Manager?**
- Make sure you're using Arduino IDE 1.8.x or 2.x (not Arduino Web Editor)
- If using Arduino IDE 2.x, the interface is slightly different but Boards Manager is in the same place

**Board Manager URL not working?**
Try this alternative ESP32 URL:
```
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
```

**Still can't find ESP32?**
1. Close and reopen Arduino IDE after adding URL
2. Try restarting your computer
3. Check your internet connection
4. Make sure you're searching for "esp32" (not "esp8266")

**Upload Errors:**
- **"Failed to connect to ESP32"**: 
  - Check USB-to-Serial adapter connections
  - Ensure GPIO 0 is LOW during boot (use IO0 button)
  - Try lowering upload speed to 115200
  - Check COM port is correct

- **"Access is denied" or "Port busy"**:
  - Close Serial Monitor
  - Close other programs using the COM port
  - Unplug and reconnect ESP32-CAM

- **"A fatal error occurred"**:
  - Check USB-to-Serial adapter (try different one)
  - Verify wiring connections
  - Try pressing Reset button during upload

### System Issues

**WiFi Connection Issues:**
- Check SSID and password in ESP32-CAM code
- Ensure 2.4GHz WiFi (ESP32-CAM doesn't support 5GHz)
- Check Serial Monitor for connection status

**Camera Issues:**
- Verify ESP32-CAM is AI Thinker model (pin configuration may differ)
- Check power supply (needs stable 5V 2A)
- See Serial Monitor for camera initialization errors

**Backend Connection Issues:**
- Verify backend server is running
- Check IP addresses match in both ESP32-CAM code and backend server
- Ensure ESP32-CAM and laptop are on the same WiFi network
- Test backend URL in browser: `http://YOUR_LAPTOP_IP:5000/health`

**Model Loading Issues:**
- Verify `model/model.tflite` and `model/labels.txt` exist
- Check TensorFlow Lite compatibility
- See backend console for error messages

**Stream Timeout:**
- Check ESP32-CAM stream URL is correct
- Verify ESP32-CAM is powered and WiFi connected
- Restart backend server if stream disconnects

### Streaming Issues

**"Failed to connect to stream":**
- Check ESP32-CAM IP address
- Verify ESP32-CAM is connected to WiFi
- Check if port 81 is accessible: `http://ESP32_IP:81/stream`
- Ensure ESP32-CAM and backend are on same network

**"Waiting for ESP32-CAM stream...":**
- Backend can't connect to ESP32-CAM
- Check `ESP32_CAM_STREAM_URL` in `backend_server.py`
- Verify ESP32-CAM streaming server is running

**Low Frame Rate:**
- Reduce `frame_skip` value (but will use more CPU)
- Reduce JPEG quality in ESP32-CAM code
- Check WiFi signal strength

**Predictions Not Updating:**
- Check backend console for errors
- Verify model is loaded correctly
- Check if frames are being received

**OpenCV Window Freezing:**
- Check if stream is still active
- Restart backend server
- Verify ESP32-CAM is powered and connected

### Network Configuration

**Firewall:**
- Ensure port 5000 is open (backend server)
- Ensure port 81 is accessible (ESP32-CAM stream)

**Router Settings:**
- Both ESP32-CAM and backend server must be on same network
- Use local IP addresses (192.168.x.x), not public IPs

### Port Selection Tips

- **Windows**: Ports appear as COM1, COM2, COM3, etc.
- **Mac**: Ports appear as /dev/cu.usbserial-xxxxx or /dev/cu.wchusbserial-xxxxx
- **Linux**: Ports appear as /dev/ttyUSB0 or /dev/ttyACM0

If you don't see a port:
- Make sure USB-to-Serial adapter is connected
- Install CH340/FTDI/CP2102 USB drivers (depending on your adapter)
- Check Device Manager (Windows) or System Information (Mac) to see if adapter is detected

---

## File Structure

```
iot/
├── backend_server.py              # Flask backend server
├── esp32_cam_controller/
│   └── esp32_cam_controller.ino  # ESP32-CAM code
├── model/
│   ├── model.tflite             # TensorFlow Lite model
│   └── labels.txt               # Model labels
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## Quick Checklist

**ESP32-CAM Setup:**
- [ ] Added ESP32 board manager URL
- [ ] Installed ESP32 board support
- [ ] Selected "AI Thinker ESP32-CAM"
- [ ] Installed ArduinoJson library
- [ ] Selected correct COM port
- [ ] Configured partition scheme (if needed)
- [ ] Enabled PSRAM
- [ ] Connected USB-to-Serial adapter correctly
- [ ] GPIO 0 set to LOW during boot (for upload mode)
- [ ] Configured WiFi credentials
- [ ] Updated backend URL in code
- [ ] Uploaded code successfully
- [ ] Noted ESP32-CAM IP address

**Backend Server Setup:**
- [ ] Installed Python dependencies (`pip install -r requirements.txt`)
- [ ] Model files in `model/` directory
- [ ] Updated `ESP32_CAM_STREAM_URL` in `backend_server.py`
- [ ] Backend server running
- [ ] OpenCV window showing stream

**Testing:**
- [ ] ESP32-CAM web interface accessible
- [ ] Material identification working
- [ ] Real-time streaming working
- [ ] Predictions displaying correctly

---

## License

This project is for educational and demonstration purposes.
#   p y t h o n - b e  
 