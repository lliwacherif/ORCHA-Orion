# Frontend OCR Integration Guide

## Overview
This guide will help you integrate OCR text extraction functionality into your React frontend. Users will be able to upload images, extract text using OCR, and display the results in a dedicated window.

---

## Architecture Flow

```
User uploads image → Frontend converts to base64 → POST to ORCHA /api/v1/orcha/ocr/extract 
→ ORCHA forwards to OCR Service → Text extracted → ORCHA returns text → Frontend displays in window
```

---

## API Endpoint

### POST `/api/v1/orcha/ocr/extract`

**Request:**
```json
{
  "user_id": "user123",
  "tenant_id": "tenant1",
  "image_data": "base64EncodedImageString",
  "filename": "document.jpg",
  "mode": "auto"
}
```

**Response (Success):**
```json
{
  "status": "success",
  "extracted_text": "This is the text extracted from the image.\nLine 2 of text.\nLine 3 of text.",
  "confidence": 0.957,
  "metadata": {
    "total_lines": 3,
    "avg_confidence": 0.957,
    "mode": "auto"
  },
  "filename": "document.jpg",
  "ocr_mode": "auto"
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

## Implementation

### 1. React Component - OCR Upload & Display

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
  const [ocrMetadata, setOcrMetadata] = useState(null);
  const [ocrMode, setOcrMode] = useState('auto'); // auto, fast, accurate

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
    setOcrMetadata(null);

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
          mode: ocrMode
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
        setOcrMetadata(response.data.metadata);
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
    // You can add a toast notification here
    alert('Text copied to clipboard!');
  };

  // Clear all
  const handleClear = () => {
    setSelectedFile(null);
    setImagePreview(null);
    setExtractedText('');
    setError(null);
    setOcrMetadata(null);
  };

  return (
    <div className="ocr-extractor">
      <div className="ocr-header">
        <h2>📸 OCR Text Extractor</h2>
        <p>Upload an image to extract text using AI-powered OCR</p>
      </div>

      {/* OCR Mode Selection */}
      <div className="ocr-mode-selector">
        <label>OCR Mode:</label>
        <select 
          value={ocrMode} 
          onChange={(e) => setOcrMode(e.target.value)}
          disabled={isLoading}
        >
          <option value="auto">Auto (Balanced)</option>
          <option value="fast">Fast (Lower accuracy)</option>
          <option value="accurate">Accurate (Slower)</option>
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
          {ocrMetadata && (
            <div className="ocr-metadata">
              <span>Lines: {ocrMetadata.total_lines}</span>
              <span>Confidence: {(ocrMetadata.avg_confidence * 100).toFixed(1)}%</span>
              <span>Mode: {ocrMetadata.mode}</span>
            </div>
          )}

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

### 2. Styling (CSS)

```css
/* components/OCRExtractor.css */
.ocr-extractor {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
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

.ocr-mode-selector {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.ocr-mode-selector label {
  font-weight: 600;
  color: #333;
}

.ocr-mode-selector select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
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

.ocr-metadata {
  padding: 10px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #ddd;
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #666;
}

.ocr-metadata span {
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

### 3. Integration with Existing App

```jsx
// App.jsx or your main router
import React from 'react';
import OCRExtractor from './components/OCRExtractor';

function App() {
  return (
    <div className="app">
      {/* Your existing components */}
      <OCRExtractor />
    </div>
  );
}

export default App;
```

### 4. Alternative: Modal/Popup Implementation

```jsx
// components/OCRModal.jsx
import React, { useState } from 'react';
import Modal from 'react-modal'; // npm install react-modal
import OCRExtractor from './OCRExtractor';

Modal.setAppElement('#root');

const OCRModal = ({ isOpen, onClose }) => {
  return (
    <Modal
      isOpen={isOpen}
      onRequestClose={onClose}
      style={{
        overlay: {
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          zIndex: 1000
        },
        content: {
          top: '50%',
          left: '50%',
          right: 'auto',
          bottom: 'auto',
          marginRight: '-50%',
          transform: 'translate(-50%, -50%)',
          maxWidth: '900px',
          width: '90%',
          maxHeight: '90vh',
          overflow: 'auto',
          padding: '30px',
          borderRadius: '12px'
        }
      }}
    >
      <button
        onClick={onClose}
        style={{
          position: 'absolute',
          top: '10px',
          right: '10px',
          background: 'none',
          border: 'none',
          fontSize: '24px',
          cursor: 'pointer'
        }}
      >
        ✕
      </button>
      <OCRExtractor />
    </Modal>
  );
};

export default OCRModal;
```

---

## Usage Examples

### Example 1: Standalone Page
```jsx
import OCRExtractor from './components/OCRExtractor';

function OCRPage() {
  return (
    <div className="container">
      <OCRExtractor />
    </div>
  );
}
```

### Example 2: As Part of Chat Interface
```jsx
function ChatInterface() {
  const [showOCR, setShowOCR] = useState(false);
  const [extractedText, setExtractedText] = useState('');

  const handleTextExtracted = (text) => {
    setExtractedText(text);
    setShowOCR(false);
    // Insert text into chat input or message
  };

  return (
    <div>
      <button onClick={() => setShowOCR(true)}>
        📸 Extract Text from Image
      </button>
      {showOCR && (
        <OCRModal 
          isOpen={showOCR} 
          onClose={() => setShowOCR(false)}
          onTextExtracted={handleTextExtracted}
        />
      )}
    </div>
  );
}
```

---

## Advanced Features

### 1. Multiple File Upload

```jsx
const [files, setFiles] = useState([]);

const handleMultipleFiles = (event) => {
  const selectedFiles = Array.from(event.target.files);
  setFiles(selectedFiles);
};

// Process all files
const extractAllTexts = async () => {
  const results = await Promise.all(
    files.map(file => extractTextFromFile(file))
  );
  // Handle results
};
```

### 2. Drag & Drop Support

```jsx
const handleDrop = (e) => {
  e.preventDefault();
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) {
    setSelectedFile(file);
  }
};

<div
  onDrop={handleDrop}
  onDragOver={(e) => e.preventDefault()}
  className="drop-zone"
>
  Drop image here
</div>
```

### 3. Save Extracted Text

```jsx
const handleSaveText = () => {
  const blob = new Blob([extractedText], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'extracted-text.txt';
  a.click();
  URL.revokeObjectURL(url);
};
```

---

## Error Handling

```jsx
const ERROR_MESSAGES = {
  'network': 'Network error. Please check your connection.',
  'timeout': 'Request timeout. Please try again.',
  'size': 'File size too large. Maximum 10MB allowed.',
  'format': 'Invalid file format. Please upload an image.',
  'ocr_failed': 'OCR processing failed. Please try a clearer image.'
};

const handleError = (error) => {
  if (error.code === 'ECONNABORTED') {
    setError(ERROR_MESSAGES.timeout);
  } else if (error.response?.status === 413) {
    setError(ERROR_MESSAGES.size);
  } else {
    setError(error.response?.data?.error || ERROR_MESSAGES.ocr_failed);
  }
};
```

---

## Testing

### Test with Sample Images

```jsx
// For development/testing
const SAMPLE_IMAGE = 'data:image/png;base64,...';

const loadSampleImage = () => {
  setImagePreview(SAMPLE_IMAGE);
  // Extract base64 part
  const base64 = SAMPLE_IMAGE.split(',')[1];
  // Process...
};
```

---

## Configuration

### Environment Variables

```bash
# .env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_MAX_FILE_SIZE=10485760  # 10MB in bytes
```

Use in code:
```jsx
const API_URL = process.env.REACT_APP_API_URL;
const MAX_FILE_SIZE = parseInt(process.env.REACT_APP_MAX_FILE_SIZE);
```

---

## Best Practices

1. **File Validation**: Always validate file type and size before upload
2. **Loading States**: Show clear loading indicators during processing
3. **Error Handling**: Provide helpful error messages to users
4. **Responsive Design**: Ensure component works on mobile devices
5. **Accessibility**: Add proper ARIA labels and keyboard navigation
6. **User Feedback**: Show confidence scores and metadata
7. **Performance**: Consider lazy loading for large images

---

## Troubleshooting

### Issue: CORS errors
**Solution**: Ensure ORCHA backend has proper CORS configuration

### Issue: Base64 too large
**Solution**: Compress image before encoding or resize on client side

### Issue: Low extraction accuracy
**Solution**: Use `mode="accurate"` or improve image quality

### Issue: Slow processing
**Solution**: Use `mode="fast"` for quicker results

---

## Next Steps

1. Implement the component in your React app
2. Test with various image types (photos, scanned documents, screenshots)
3. Customize styling to match your app's theme
4. Add additional features (history, batch processing, etc.)
5. Monitor performance and user feedback

For OCR service setup, see `OCR_SERVICE_GUIDE.md`.





