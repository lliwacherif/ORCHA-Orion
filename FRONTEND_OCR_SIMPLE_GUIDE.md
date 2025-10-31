# Frontend OCR Integration Guide

## 🎯 Overview

This guide shows you how to implement OCR text extraction in your React frontend. Users can upload images, extract text using OCR, and display the results.

---

## 🔄 Flow

```
1. User selects image → 2. Convert to base64 → 3. Send to ORCHA → 4. ORCHA sends to OCR Service → 5. OCR extracts text → 6. Text returned to frontend → 7. Display in window
```

---

## 📡 API Endpoint

**URL:** `POST /api/v1/orcha/ocr/extract`

**Request:**
```json
{
  "user_id": "user123",
  "image_data": "base64EncodedImageString",
  "filename": "document.jpg",
  "language": "en"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "extracted_text": "Text extracted from image\nLine 2\nLine 3",
  "lines_count": 3,
  "message": "Text extracted successfully",
  "filename": "document.jpg",
  "language": "en"
}
```

**Response (Error):**
```json
{
  "status": "error",
  "error": "Error message",
  "filename": "document.jpg"
}
```

---

## 🚀 React Implementation

### 1. Complete OCR Component

```jsx
// components/OCRExtractor.jsx
import React, { useState } from 'react';
import axios from 'axios';

const OCRExtractor = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [extractedText, setExtractedText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [linesCount, setLinesCount] = useState(0);
  const [language, setLanguage] = useState('en');

  // Available languages
  const languages = [
    { code: 'en', name: 'English' },
    { code: 'fr', name: 'French' },
    { code: 'ar', name: 'Arabic' },
    { code: 'ch', name: 'Chinese' },
    { code: 'es', name: 'Spanish' },
    { code: 'de', name: 'German' },
    { code: 'it', name: 'Italian' },
    { code: 'pt', name: 'Portuguese' },
    { code: 'ru', name: 'Russian' },
    { code: 'ja', name: 'Japanese' },
    { code: 'ko', name: 'Korean' }
  ];

  // Handle file selection
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    setSelectedFile(file);
    setError(null);
    setExtractedText('');
    setLinesCount(0);

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  // Convert file to base64
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        // Remove the data URL prefix (data:image/jpeg;base64,)
        const base64String = reader.result.split(',')[1];
        resolve(base64String);
      };
      reader.onerror = (error) => reject(error);
    });
  };

  // Extract text from image
  const handleExtractText = async () => {
    if (!selectedFile) {
      setError('Please select an image first');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Convert image to base64
      const base64Image = await fileToBase64(selectedFile);

      // Get user_id from your auth context/localStorage
      const userId = localStorage.getItem('user_id') || 'anonymous';
      const tenantId = localStorage.getItem('tenant_id') || null;

      // Send request to ORCHA
      const response = await axios.post(
        'http://localhost:8000/api/v1/orcha/ocr/extract',
        {
          user_id: userId,
          tenant_id: tenantId,
          image_data: base64Image,
          filename: selectedFile.name,
          language: language
        },
        {
          headers: {
            'Content-Type': 'application/json',
            // Add auth token if required
            // 'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      if (response.data.status === 'success') {
        setExtractedText(response.data.extracted_text);
        setLinesCount(response.data.lines_count);
      } else {
        setError(response.data.error || 'OCR extraction failed');
      }
    } catch (err) {
      console.error('OCR extraction error:', err);
      setError(
        err.response?.data?.detail || 
        err.response?.data?.error || 
        'Failed to extract text from image'
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Copy text to clipboard
  const handleCopyText = () => {
    navigator.clipboard.writeText(extractedText);
    alert('Text copied to clipboard!');
  };

  // Clear all
  const handleClear = () => {
    setSelectedFile(null);
    setImagePreview(null);
    setExtractedText('');
    setError(null);
    setLinesCount(0);
  };

  return (
    <div className="ocr-extractor">
      <div className="ocr-header">
        <h2>📸 OCR Text Extractor</h2>
        <p>Upload an image to extract text using AI-powered OCR</p>
      </div>

      {/* Language Selection */}
      <div className="language-selector">
        <label>Language:</label>
        <select 
          value={language} 
          onChange={(e) => setLanguage(e.target.value)}
          disabled={isLoading}
        >
          {languages.map(lang => (
            <option key={lang.code} value={lang.code}>
              {lang.name}
            </option>
          ))}
        </select>
      </div>

      {/* File Upload */}
      <div className="upload-section">
        <input
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          disabled={isLoading}
          id="file-input"
          style={{ display: 'none' }}
        />
        <label htmlFor="file-input" className="upload-button">
          📁 Choose Image
        </label>
        {selectedFile && (
          <span className="file-name">{selectedFile.name}</span>
        )}
      </div>

      {/* Image Preview */}
      {imagePreview && (
        <div className="image-preview">
          <h3>Image Preview</h3>
          <img src={imagePreview} alt="Preview" style={{ maxWidth: '100%', maxHeight: '400px' }} />
        </div>
      )}

      {/* Action Buttons */}
      <div className="action-buttons">
        <button
          onClick={handleExtractText}
          disabled={!selectedFile || isLoading}
          className="extract-button"
        >
          {isLoading ? '⏳ Extracting...' : '🔍 Extract Text'}
        </button>
        {(extractedText || error) && (
          <button onClick={handleClear} className="clear-button">
            🗑️ Clear
          </button>
        )}
      </div>

      {/* Loading Indicator */}
      {isLoading && (
        <div className="loading-indicator">
          <div className="spinner"></div>
          <p>Processing image... This may take a few seconds.</p>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-message">
          <strong>❌ Error:</strong> {error}
        </div>
      )}

      {/* Extracted Text Display */}
      {extractedText && (
        <div className="extracted-text-container">
          <div className="text-header">
            <h3>✅ Extracted Text</h3>
            <button onClick={handleCopyText} className="copy-button">
              📋 Copy
            </button>
          </div>
          
          {/* Metadata */}
          <div className="text-metadata">
            <span>Lines: {linesCount}</span>
            <span>Language: {languages.find(l => l.code === language)?.name}</span>
            <span>Filename: {selectedFile?.name}</span>
          </div>

          {/* Text Display */}
          <div className="text-display">
            <pre>{extractedText}</pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default OCRExtractor;
```

### 2. CSS Styling

```css
/* components/OCRExtractor.css */
.ocr-extractor {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.ocr-header {
  text-align: center;
  margin-bottom: 30px;
}

.ocr-header h2 {
  font-size: 28px;
  margin-bottom: 10px;
  color: #333;
}

.ocr-header p {
  color: #666;
  font-size: 14px;
}

.language-selector {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.language-selector label {
  font-weight: 600;
  color: #333;
}

.language-selector select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  min-width: 120px;
}

.upload-section {
  margin-bottom: 20px;
  text-align: center;
}

.upload-button {
  display: inline-block;
  padding: 12px 24px;
  background: #007bff;
  color: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  transition: background 0.3s;
}

.upload-button:hover {
  background: #0056b3;
}

.file-name {
  margin-left: 15px;
  color: #666;
  font-size: 14px;
}

.image-preview {
  margin: 20px 0;
  padding: 20px;
  border: 2px dashed #ddd;
  border-radius: 8px;
  text-align: center;
}

.image-preview h3 {
  margin-bottom: 15px;
  color: #333;
}

.action-buttons {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin: 20px 0;
}

.extract-button, .clear-button {
  padding: 12px 30px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.extract-button {
  background: #28a745;
  color: white;
}

.extract-button:hover:not(:disabled) {
  background: #218838;
}

.extract-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.clear-button {
  background: #dc3545;
  color: white;
}

.clear-button:hover {
  background: #c82333;
}

.loading-indicator {
  text-align: center;
  padding: 30px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  padding: 15px;
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 8px;
  color: #721c24;
  margin: 20px 0;
}

.extracted-text-container {
  margin-top: 30px;
  border: 2px solid #28a745;
  border-radius: 8px;
  overflow: hidden;
}

.text-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: #28a745;
  color: white;
}

.text-header h3 {
  margin: 0;
  font-size: 18px;
}

.copy-button {
  padding: 8px 16px;
  background: white;
  color: #28a745;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.3s;
}

.copy-button:hover {
  background: #f0f0f0;
}

.text-metadata {
  padding: 10px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #ddd;
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #666;
}

.text-metadata span {
  font-weight: 600;
}

.text-display {
  padding: 20px;
  background: white;
  max-height: 500px;
  overflow-y: auto;
}

.text-display pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}
```

### 3. Usage in Your App

```jsx
// App.jsx
import React from 'react';
import OCRExtractor from './components/OCRExtractor';
import './components/OCRExtractor.css';

function App() {
  return (
    <div className="app">
      <OCRExtractor />
    </div>
  );
}

export default App;
```

---

## 🧪 Testing

### 1. Test with cURL

```bash
# First, convert an image to base64
base64 your_image.jpg > image_b64.txt

# Then test the endpoint
curl -X POST http://localhost:8000/api/v1/orcha/ocr/extract \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "image_data": "'$(cat image_b64.txt)'",
    "filename": "test.jpg",
    "language": "en"
  }'
```

### 2. Test with Python

```bash
# Run the integration test
python test_orcha_ocr_integration.py
```

---

## 🌍 Supported Languages

| Code | Language |
|------|----------|
| `en` | English |
| `fr` | French |
| `ar` | Arabic |
| `ch` | Chinese |
| `es` | Spanish |
| `de` | German |
| `it` | Italian |
| `pt` | Portuguese |
| `ru` | Russian |
| `ja` | Japanese |
| `ko` | Korean |

---

## 🔧 Configuration

### Environment Variables

```bash
# .env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_MAX_FILE_SIZE=10485760  # 10MB
```

Use in code:
```jsx
const API_URL = process.env.REACT_APP_API_URL;
const MAX_FILE_SIZE = parseInt(process.env.REACT_APP_MAX_FILE_SIZE);
```

---

## 🐛 Troubleshooting

### CORS Errors
Add CORS middleware to ORCHA:
```python
# In app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Connection Errors
- Make sure ORCHA is running on port 8000
- Make sure OCR service is running on port 8001
- Check the URLs in your frontend code

### Low Accuracy
- Use higher resolution images
- Select the correct language
- Ensure text is clearly visible

---

## 🎯 Quick Start Checklist

- [ ] Copy the React component code
- [ ] Add the CSS styling
- [ ] Install axios: `npm install axios`
- [ ] Start ORCHA: `uvicorn app.main:app --reload --port 8000`
- [ ] Start OCR service: `python app.py`
- [ ] Test with sample image
- [ ] Deploy to production

---

## 🎉 You're Ready!

The integration is complete. Users can now:
1. Upload images
2. Select language
3. Extract text
4. Copy results
5. View metadata

Good luck! 🚀




