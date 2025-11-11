# API Testing Examples for /identify/material

## 1. Using curl (if you have curl installed)
curl -X POST http://localhost:5001/identify/material \
  -H "Content-Type: image/jpeg" \
  --data-binary "@test_image.jpg"

## 2. Using PowerShell
Invoke-WebRequest -Uri "http://localhost:5001/identify/material" `
  -Method Post `
  -InFile "test_image.jpg" `
  -ContentType "image/jpeg"

## 3. Using Python requests
python test_api.py test_image.jpg

## 4. Using PowerShell script
.\test_api.ps1 test_image.jpg

## Expected Response Format:
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

## Actions returned:
- "sort_plastic" - for Plastic Bottle
- "sort_tin_can" - for Tin Can
- "reject" - for Other or Unknown materials
