/*
 * ESP32-CAM Controller for Recycling Machine
 * Standalone controller working directly with backend server
 * With built-in streaming server for real-time monitoring
 * 
 * Features:
 * - Live video streaming on port 81
 * - Web interface to trigger material identification
 * - Direct communication with backend server for AI classification
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <WebServer.h>

// WiFi Configuration
const char* ssid = "PLDT_Home_7CB79";
const char* password = "Hayao1014";

// Backend Server URL (Updated to match current computer IP and new port)
const char* IDENTIFICATION_BACKEND_URL = "http://192.168.1.31:5001/identify/material";

// Streaming Server (port 81)
WebServer server(81);

// Camera Model (ESP32-CAM AI Thinker)
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// Timing
const unsigned long CAPTURE_COOLDOWN = 2000; // 2 seconds between captures
unsigned long lastCaptureTime = 0;

// Latest identification result
String lastMaterialType = "None";
float lastConfidence = 0.0;
String lastAction = "";

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("ESP32-CAM Recycling Machine Controller");
  Serial.println("Standalone Mode - Direct Backend Integration");
  
  // Initialize camera
  initializeCamera();
  
  // Connect to WiFi
  connectToWiFi();
  
  // Setup streaming server
  setupStreamingServer();
  
  Serial.println("System ready!");
  Serial.print("Stream available at: http://");
  Serial.print(WiFi.localIP());
  Serial.println(":81/stream");
  Serial.print("Web interface at: http://");
  Serial.print(WiFi.localIP());
  Serial.println(":81");
  Serial.println("Trigger identification: http://" + WiFi.localIP().toString() + ":81/capture");
}

void loop() {
  // Handle web server requests (streaming and identification)
  server.handleClient();
  
  delay(10); // Small delay for stability
}

void initializeCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_VGA;  // 640x480 for streaming
  config.pixel_format = PIXFORMAT_JPEG;
  config.jpeg_quality = 12;  // Lower = higher quality, 10-63
  config.fb_count = 1;
  config.grab_mode = CAMERA_GRAB_LATEST;
  
  // Camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return;
  }
  
  Serial.println("Camera initialized successfully");
}

void connectToWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("");
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("");
    Serial.println("WiFi connection failed!");
  }
}

void setupStreamingServer() {
  // Root page - enhanced HTML interface with identification trigger
  server.on("/", HTTP_GET, handleRoot);
  
  // MJPEG stream endpoint
  server.on("/stream", HTTP_GET, handleStream);
  
  // Status endpoint
  server.on("/status", HTTP_GET, handleStatus);
  
  // Capture and identify endpoint
  server.on("/capture", HTTP_GET, handleCapture);
  
  // Get last result endpoint
  server.on("/result", HTTP_GET, handleResult);
  
  // Start server
  server.begin();
  Serial.println("HTTP server started on port 81");
}

void handleRoot() {
  String html = "<!DOCTYPE html><html><head><title>ESP32-CAM Recycling Machine</title>";
  html += "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">";
  html += "<style>";
  html += "body {font-family: Arial; text-align: center; background: #1a1a1a; color: white; margin: 0; padding: 20px;}";
  html += "img {max-width: 100%; border: 2px solid #00ff00; border-radius: 10px;}";
  html += ".container {max-width: 1200px; margin: 0 auto;}";
  html += ".button {background: #4CAF50; color: white; padding: 15px 30px; border: none; border-radius: 5px; font-size: 18px; cursor: pointer; margin: 10px;}";
  html += ".button:hover {background: #45a049;}";
  html += ".button:active {background: #3d8b40;}";
  html += ".result {background: #2a2a2a; padding: 20px; margin: 20px; border-radius: 5px; border: 2px solid #444;}";
  html += ".result h2 {color: #4CAF50; margin-top: 0;}";
  html += ".info {color: #aaa; font-size: 14px;}";
  html += "</style></head><body>";
  html += "<div class=\"container\">";
  html += "<h1>ESP32-CAM Recycling Machine</h1>";
  html += "<img src=\"/stream\" alt=\"Video Stream\">";
  html += "<div>";
  html += "<button class=\"button\" onclick=\"captureAndIdentify()\">🔍 Identify Material</button>";
  html += "<button class=\"button\" onclick=\"location.reload()\">🔄 Refresh</button>";
  html += "</div>";
  html += "<div class=\"result\" id=\"result\">";
  html += "<h2>Last Identification Result</h2>";
  html += "<p><strong>Material:</strong> <span id=\"material\">" + lastMaterialType + "</span></p>";
  html += "<p><strong>Confidence:</strong> <span id=\"confidence\">" + String(lastConfidence * 100, 1) + "%</span></p>";
  html += "<p><strong>Action:</strong> <span id=\"action\">" + lastAction + "</span></p>";
  html += "</div>";
  html += "<div class=\"info\">";
  html += "<p><a href=\"/status\" style=\"color: #4CAF50;\">Status</a> | <a href=\"/result\" style=\"color: #4CAF50;\">API Result</a></p>";
  html += "</div>";
  html += "</div>";
  html += "<script>";
  html += "function captureAndIdentify() {";
  html += "  document.getElementById('result').innerHTML = '<h2>Processing...</h2><p>Capturing image and identifying material...</p>';";
  html += "  fetch('/capture')";
  html += "    .then(response => response.json())";
  html += "    .then(data => {";
  html += "      if (data.success) {";
  html += "        document.getElementById('material').textContent = data.materialType;";
  html += "        document.getElementById('confidence').textContent = (data.confidence * 100).toFixed(1) + '%';";
  html += "        document.getElementById('action').textContent = data.action;";
  html += "        document.getElementById('result').innerHTML = '<h2>✓ Identification Complete</h2><p><strong>Material:</strong> ' + data.materialType + '</p><p><strong>Confidence:</strong> ' + (data.confidence * 100).toFixed(1) + '%</p><p><strong>Action:</strong> ' + data.action + '</p>';";
  html += "      } else {";
  html += "        document.getElementById('result').innerHTML = '<h2>✗ Error</h2><p>' + (data.error || 'Identification failed') + '</p>';";
  html += "      }";
  html += "    })";
  html += "    .catch(error => {";
  html += "      document.getElementById('result').innerHTML = '<h2>✗ Error</h2><p>Failed to communicate with server: ' + error + '</p>';";
  html += "    });";
  html += "}";
  html += "// Auto-refresh result every 5 seconds";
  html += "setInterval(function() { fetch('/result').then(r => r.json()).then(data => {";
  html += "  if (data.materialType !== 'None') {";
  html += "    document.getElementById('material').textContent = data.materialType;";
  html += "    document.getElementById('confidence').textContent = (data.confidence * 100).toFixed(1) + '%';";
  html += "    document.getElementById('action').textContent = data.action;";
  html += "  }";
  html += "}); }, 5000);";
  html += "</script>";
  html += "</body></html>";
  server.send(200, "text/html", html);
}

void handleStream() {
  Serial.println("New stream client");
  
  WiFiClient client = server.client();
  String response = "HTTP/1.1 200 OK\r\n";
  response += "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n";
  server.sendContent(response);
  
  while (client.connected()) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      break;
    }
    
    client.print("--frame\r\n");
    client.print("Content-Type: image/jpeg\r\n");
    client.print("Content-Length: " + String(fb->len) + "\r\n\r\n");
    client.write(fb->buf, fb->len);
    client.print("\r\n");
    
    esp_camera_fb_return(fb);
    
    // Small delay to control frame rate
    delay(33); // ~30 FPS
  }
  
  Serial.println("Stream client disconnected");
}

void handleStatus() {
  String json = "{";
  json += "\"ip\":\"" + WiFi.localIP().toString() + "\",";
  json += "\"rssi\":" + String(WiFi.RSSI()) + ",";
  json += "\"status\":\"connected\"";
  json += "}";
  server.send(200, "application/json", json);
}

void handleCapture() {
  Serial.println("Capture request received via web interface");
  
  // Check cooldown
  unsigned long currentTime = millis();
  if (currentTime - lastCaptureTime < CAPTURE_COOLDOWN) {
    unsigned long remaining = (CAPTURE_COOLDOWN - (currentTime - lastCaptureTime)) / 1000;
    String response = "{\"success\":false,\"error\":\"Cooldown active. Please wait " + String(remaining) + " seconds.\"}";
    server.send(200, "application/json", response);
    return;
  }
  
  lastCaptureTime = currentTime;
  
  // Capture and identify
  bool success = captureAndIdentify();
  
  if (success) {
    String json = "{";
    json += "\"success\":true,";
    json += "\"materialType\":\"" + lastMaterialType + "\",";
    json += "\"confidence\":" + String(lastConfidence) + ",";
    json += "\"action\":\"" + lastAction + "\"";
    json += "}";
    server.send(200, "application/json", json);
  } else {
    String json = "{\"success\":false,\"error\":\"Failed to capture or identify\"}";
    server.send(200, "application/json", json);
  }
}

void handleResult() {
  String json = "{";
  json += "\"materialType\":\"" + lastMaterialType + "\",";
  json += "\"confidence\":" + String(lastConfidence) + ",";
  json += "\"action\":\"" + lastAction + "\"";
  json += "}";
  server.send(200, "application/json", json);
}

bool captureAndIdentify() {
  // Check WiFi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected - cannot identify material");
    lastMaterialType = "Error";
    lastConfidence = 0.0;
    lastAction = "WiFi disconnected";
    return false;
  }
  
  Serial.println("Capturing image...");
  
  // Capture frame
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("ERROR: Camera capture failed");
    lastMaterialType = "Error";
    lastConfidence = 0.0;
    lastAction = "Camera capture failed";
    return false;
  }
  
  Serial.printf("Image captured: %d bytes\n", fb->len);
  
  // Send image to Identification Backend
  HTTPClient http;
  http.setTimeout(10000); // 10 second timeout
  http.begin(IDENTIFICATION_BACKEND_URL);
  http.addHeader("Content-Type", "image/jpeg");
  
  int httpResponseCode = http.POST(fb->buf, fb->len);
  
  // Return frame buffer immediately after sending
  esp_camera_fb_return(fb);
  
  bool success = false;
  
  if (httpResponseCode > 0) {
    Serial.printf("Backend response code: %d\n", httpResponseCode);
    
    if (httpResponseCode == 200) {
      String response = http.getString();
      Serial.println("Backend response: " + response);
      
      // Parse JSON response
      DynamicJsonDocument doc(1024);
      DeserializationError error = deserializeJson(doc, response);
      
      if (!error && doc["success"] == true) {
        lastMaterialType = doc["materialType"] | "Unknown";
        lastConfidence = doc["confidence"] | 0.0;
        lastAction = doc["action"] | "unknown";
        
        Serial.printf("✓ Material identified: %s (confidence: %.2f)\n", lastMaterialType.c_str(), lastConfidence);
        Serial.printf("  Action: %s\n", lastAction.c_str());
        
        success = true;
      } else {
        Serial.println("Failed to parse backend response");
        lastMaterialType = "Error";
        lastConfidence = 0.0;
        lastAction = "Parse error";
      }
    } else {
      Serial.printf("Backend returned non-200 code: %d\n", httpResponseCode);
      lastMaterialType = "Error";
      lastConfidence = 0.0;
      lastAction = "HTTP " + String(httpResponseCode);
    }
  } else {
    Serial.printf("Backend connection failed! Error code: %d\n", httpResponseCode);
    lastMaterialType = "Error";
    lastConfidence = 0.0;
    lastAction = "Connection failed";
  }
  
  http.end();
  
  return success;
}
