# Postman Testing Guide for Material Identification API

## Quick Start

### Import Postman Collection
1. Open Postman
2. Click **Import** button (top left)
3. Select **Postman_Collection.json** from this folder
4. All endpoints will be loaded automatically

---

## Method 1: Binary Image Upload (EASIEST)

### Steps:
1. **Create new request** in Postman
2. **Set method:** `POST`
3. **Set URL:** `http://localhost:5001/identify/material`
4. **Headers tab:**
   - Key: `Content-Type`
   - Value: `image/jpeg`
5. **Body tab:**
   - Select **binary**
   - Click **Select File**
   - Choose your JPEG image
6. **Click Send**

### Expected Response:
```json
{
  "success": true,
  "materialType": "Plastic Bottle",
  "confidence": 0.95,
  "action": "sort_plastic",
  "allPredictions": {
    "Plastic Bottle": 0.95,
    "Tin Can": 0.03,
    "Other": 0.02
  }
}
```

---

## Method 2: Base64 JSON Upload

### Steps:
1. **Encode your image to base64:**
   ```powershell
   python encode_image_base64.py test_image.jpg
   ```
   This will output the base64 string and save it to `base64_image.txt`

2. **Create new request** in Postman
3. **Set method:** `POST`
4. **Set URL:** `http://localhost:5001/identify/material`
5. **Headers tab:**
   - Key: `Content-Type`
   - Value: `application/json`
6. **Body tab:**
   - Select **raw**
   - Choose **JSON** from dropdown
   - Paste:
   ```json
   {
     "image": "PASTE_BASE64_STRING_HERE"
   }
   ```
7. **Click Send**

---

## Available Endpoints

### 1. Health Check
- **Method:** GET
- **URL:** `http://localhost:5001/health`
- **Description:** Check server status and model availability

### 2. Test Endpoint
- **Method:** GET
- **URL:** `http://localhost:5001/identify/test`
- **Description:** Verify API is accessible

### 3. Get Latest Prediction
- **Method:** GET
- **URL:** `http://localhost:5001/prediction`
- **Description:** Get latest prediction from real-time stream

### 4. Identify Material
- **Method:** POST
- **URL:** `http://localhost:5001/identify/material`
- **Content-Type:** `image/jpeg` OR `application/json`
- **Description:** Send image for material identification

### 5. Bin Update (Optional)
- **Method:** POST
- **URL:** `http://localhost:5001/bin/update`
- **Content-Type:** `application/json`
- **Description:** Send bin level updates

---

## Response Format

### Success Response:
```json
{
  "success": true,
  "materialType": "Plastic Bottle" | "Tin Can" | "Other",
  "confidence": 0.95,
  "action": "sort_plastic" | "sort_tin_can" | "reject",
  "allPredictions": {
    "Plastic Bottle": 0.95,
    "Tin Can": 0.03,
    "Other": 0.02
  }
}
```

### Error Response:
```json
{
  "success": false,
  "error": "Error message description"
}
```

---

## Troubleshooting

### Error: Cannot connect to server
- Make sure backend server is running: `python backend_server.py`
- Check if server is on port 5001: `http://localhost:5001`

### Error: Model not loaded
- Verify model files exist in `model/` folder
- Check `model/model.tflite` and `model/labels.txt`

### Error: No image data received
- For binary: Make sure you selected a file in Body > binary
- For JSON: Verify base64 string is properly formatted

### Error: Invalid image format
- Ensure image is in JPEG format
- Try converting with: `convert image.png image.jpg` (ImageMagick)

---

## Tips

1. **Use binary upload** for simplicity (Method 1)
2. **Import the collection** (`Postman_Collection.json`) for pre-configured requests
3. **Check /health** endpoint first to verify server is running
4. **Test with different images** to see confidence scores
5. **Look at allPredictions** to see scores for all material types

---

## Example CURL Commands (Alternative to Postman)

### Binary upload:
```bash
curl -X POST http://localhost:5001/identify/material \
  -H "Content-Type: image/jpeg" \
  --data-binary "@test_image.jpg"
```

### PowerShell:
```powershell
Invoke-WebRequest -Uri "http://localhost:5001/identify/material" `
  -Method Post `
  -InFile "test_image.jpg" `
  -ContentType "image/jpeg"
```
