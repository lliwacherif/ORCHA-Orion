# Frontend Image Attachment Examples

## Quick Start

This guide shows exactly how to send image attachments from your frontend to get vision-powered responses from Gemma.

---

## Example 1: Single Image with Text

### Frontend Request

```javascript
// Convert file to base64
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      // Strip the data URL prefix to get pure base64
      const base64 = reader.result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
  });
};

// Send request with image
const sendImageMessage = async (message, imageFile) => {
  const base64Image = await fileToBase64(imageFile);
  
  const payload = {
    message: message,
    user_id: currentUser.id,
    conversation_id: currentConversation.id, // optional
    attachments: [
      {
        type: "image",
        mime: imageFile.type,  // e.g., "image/jpeg"
        base64: base64Image,   // Pure base64 string (no data URL prefix)
        filename: imageFile.name
      }
    ]
  };
  
  const response = await fetch('/api/v1/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });
  
  return response.json();
};

// Usage
const imageFile = document.getElementById('file-input').files[0];
const result = await sendImageMessage("What do you see in this image?", imageFile);
console.log(result.message); // Gemma's vision response
```

### Backend Response

```json
{
  "status": "ok",
  "message": "I can see a sunset over the ocean with orange and pink hues in the sky...",
  "conversation_id": 42,
  "attachments_processed": 1,
  "vision_processed": true,
  "images_count": 1,
  "model_used": "google/gemma-3-12b",
  "image_filenames": ["sunset.jpg"],
  "token_usage": {
    "current_usage": 1250,
    "limit": 100000,
    "reset_at": "2025-11-04T14:30:00Z"
  }
}
```

---

## Example 2: Multiple Images

### Frontend Request

```javascript
const sendMultipleImages = async (message, imageFiles) => {
  // Convert all images to base64
  const attachments = await Promise.all(
    Array.from(imageFiles).map(async (file) => ({
      type: "image",
      mime: file.type,
      base64: await fileToBase64(file),
      filename: file.name
    }))
  );
  
  const payload = {
    message: message,
    user_id: currentUser.id,
    attachments: attachments
  };
  
  const response = await fetch('/api/v1/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });
  
  return response.json();
};

// Usage
const imageFiles = document.getElementById('file-input').files;
const result = await sendMultipleImages(
  "Compare these images and tell me the differences",
  imageFiles
);
```

### Backend Response

```json
{
  "status": "ok",
  "message": "The first image shows a daytime scene with bright sunlight, while the second image depicts the same location at night with artificial lighting...",
  "conversation_id": 42,
  "attachments_processed": 2,
  "vision_processed": true,
  "images_count": 2,
  "model_used": "google/gemma-3-12b",
  "image_filenames": ["photo1.jpg", "photo2.jpg"],
  "token_usage": {...}
}
```

---

## Example 3: Image Only (No Text)

### Frontend Request

```javascript
const sendImageOnly = async (imageFile) => {
  const base64Image = await fileToBase64(imageFile);
  
  const payload = {
    message: "",  // Empty message
    user_id: currentUser.id,
    attachments: [
      {
        type: "image",
        base64: base64Image,
        filename: imageFile.name
      }
    ]
  };
  
  const response = await fetch('/api/v1/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });
  
  return response.json();
};
```

**Backend Behavior:** Automatically adds "User provided image; analyze it" as the prompt.

### Backend Response

```json
{
  "status": "ok",
  "message": "This image contains a detailed architectural blueprint showing...",
  "conversation_id": 42,
  "vision_processed": true,
  "images_count": 1,
  "model_used": "google/gemma-3-12b"
}
```

---

## Example 4: React Component (Complete)

```jsx
import React, { useState } from 'react';

const ImageChatComponent = () => {
  const [message, setMessage] = useState('');
  const [images, setImages] = useState([]);
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleImageUpload = (e) => {
    const files = Array.from(e.target.files);
    setImages(files);
  };

  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
    });
  };

  const sendMessage = async () => {
    setLoading(true);
    
    try {
      // Convert images to base64
      const attachments = await Promise.all(
        images.map(async (file) => ({
          type: "image",
          mime: file.type,
          base64: await fileToBase64(file),
          filename: file.name
        }))
      );

      const payload = {
        message: message,
        user_id: localStorage.getItem('user_id'),
        conversation_id: localStorage.getItem('current_conversation_id'),
        attachments: attachments
      };

      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      setResponse(data);
      
      // Show which model was used
      if (data.vision_processed) {
        console.log(`✨ Vision processed by ${data.model_used}`);
        console.log(`📷 Images: ${data.images_count}`);
      }
      
      // Clear inputs
      setMessage('');
      setImages([]);
      
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="input-area">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type your message..."
        />
        
        <input
          type="file"
          accept="image/*"
          multiple
          onChange={handleImageUpload}
        />
        
        {images.length > 0 && (
          <div className="preview">
            {images.map((img, idx) => (
              <span key={idx}>{img.name}</span>
            ))}
          </div>
        )}
        
        <button 
          onClick={sendMessage} 
          disabled={loading || (images.length === 0 && !message)}
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>

      {response && (
        <div className="response-area">
          {response.vision_processed && (
            <div className="metadata">
              ✨ Vision Analysis
              📷 {response.images_count} image(s) processed
              🤖 Model: {response.model_used}
            </div>
          )}
          
          <div className="message">
            {response.message}
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageChatComponent;
```

---

## Example 5: Using FormData (Alternative)

If you prefer using `FormData` (backend would need adjustment):

```javascript
const sendWithFormData = async (message, imageFiles) => {
  const formData = new FormData();
  formData.append('message', message);
  formData.append('user_id', currentUser.id);
  
  // Append multiple images
  for (let i = 0; i < imageFiles.length; i++) {
    formData.append('images', imageFiles[i]);
  }
  
  const response = await fetch('/api/v1/chat', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  return response.json();
};
```

**Note:** Current backend expects JSON with base64-encoded images, not FormData. This is an alternative approach if you modify the backend.

---

## Example 6: Drag and Drop

```javascript
const ImageDropZone = () => {
  const [dragActive, setDragActive] = useState(false);
  
  const handleDrop = async (e) => {
    e.preventDefault();
    setDragActive(false);
    
    const files = Array.from(e.dataTransfer.files).filter(
      file => file.type.startsWith('image/')
    );
    
    if (files.length > 0) {
      // Convert to base64 and send
      const attachments = await Promise.all(
        files.map(async (file) => ({
          type: "image",
          mime: file.type,
          base64: await fileToBase64(file),
          filename: file.name
        }))
      );
      
      const payload = {
        message: "Analyze these images",
        user_id: currentUser.id,
        attachments: attachments
      };
      
      const response = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      
      const result = await response.json();
      console.log(result.message);
    }
  };
  
  return (
    <div
      className={`drop-zone ${dragActive ? 'active' : ''}`}
      onDrop={handleDrop}
      onDragOver={(e) => {
        e.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
    >
      Drop images here
    </div>
  );
};
```

---

## Example 7: Camera Capture (Mobile)

```javascript
const CameraCapture = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  
  const startCamera = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ 
      video: { facingMode: 'environment' } 
    });
    videoRef.current.srcObject = stream;
  };
  
  const captureAndSend = async () => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    
    // Draw video frame to canvas
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    
    // Convert to base64
    const base64Image = canvas.toDataURL('image/jpeg').split(',')[1];
    
    const payload = {
      message: "What do you see?",
      user_id: currentUser.id,
      attachments: [
        {
          type: "image",
          mime: "image/jpeg",
          base64: base64Image,
          filename: "camera_capture.jpg"
        }
      ]
    };
    
    const response = await fetch('/api/v1/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });
    
    const result = await response.json();
    console.log(result.message);
  };
  
  return (
    <div>
      <video ref={videoRef} autoPlay />
      <canvas ref={canvasRef} style={{ display: 'none' }} />
      <button onClick={startCamera}>Start Camera</button>
      <button onClick={captureAndSend}>Capture & Analyze</button>
    </div>
  );
};
```

---

## Response Handling

### Check if Vision was Used

```javascript
const response = await sendImageMessage(message, image);

if (response.vision_processed) {
  console.log('✨ Vision model was used!');
  console.log(`Model: ${response.model_used}`);
  console.log(`Images: ${response.images_count}`);
  console.log(`Files: ${response.image_filenames.join(', ')}`);
} else {
  console.log('📝 Text-only model was used');
}
```

### Display Vision Metadata in UI

```jsx
{response.vision_processed && (
  <div className="vision-badge">
    <span className="icon">🎨</span>
    <span className="text">Vision Analysis</span>
    <span className="model">{response.model_used}</span>
    <span className="count">{response.images_count} image(s)</span>
  </div>
)}
```

---

## Error Handling

```javascript
const sendImage = async (message, image) => {
  try {
    const base64 = await fileToBase64(image);
    
    const payload = {
      message: message,
      user_id: currentUser.id,
      attachments: [{
        type: "image",
        base64: base64,
        filename: image.name
      }]
    };
    
    const response = await fetch('/api/v1/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    
    if (result.status === 'error') {
      throw new Error(result.error);
    }
    
    return result;
    
  } catch (error) {
    console.error('Error sending image:', error);
    
    // Show user-friendly error
    if (error.message.includes('401')) {
      alert('Session expired. Please log in again.');
    } else if (error.message.includes('413')) {
      alert('Image too large. Please use a smaller image.');
    } else {
      alert('Failed to send image. Please try again.');
    }
    
    throw error;
  }
};
```

---

## Best Practices

### 1. Image Size Limits
```javascript
const MAX_IMAGE_SIZE = 5 * 1024 * 1024; // 5MB

const validateImage = (file) => {
  if (file.size > MAX_IMAGE_SIZE) {
    alert('Image must be smaller than 5MB');
    return false;
  }
  
  if (!file.type.startsWith('image/')) {
    alert('File must be an image');
    return false;
  }
  
  return true;
};
```

### 2. Image Compression (Optional)
```javascript
const compressImage = (file, maxWidth = 1920) => {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const scale = maxWidth / img.width;
        canvas.width = maxWidth;
        canvas.height = img.height * scale;
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        
        canvas.toBlob((blob) => {
          resolve(new File([blob], file.name, { type: 'image/jpeg' }));
        }, 'image/jpeg', 0.8);
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
};

// Usage
const compressedImage = await compressImage(originalFile);
await sendImageMessage(message, compressedImage);
```

### 3. Loading States
```jsx
const [uploadProgress, setUploadProgress] = useState(0);

const sendWithProgress = async (message, images) => {
  setUploadProgress(0);
  
  // Simulate progress (real implementation would use xhr progress events)
  const interval = setInterval(() => {
    setUploadProgress(prev => Math.min(prev + 10, 90));
  }, 200);
  
  try {
    const result = await sendImageMessage(message, images);
    setUploadProgress(100);
    setTimeout(() => setUploadProgress(0), 1000);
    return result;
  } finally {
    clearInterval(interval);
  }
};
```

---

## Debugging

### Log Payload Before Sending
```javascript
const payload = {
  message: message,
  user_id: currentUser.id,
  attachments: attachments
};

console.log('Sending payload:', {
  ...payload,
  attachments: payload.attachments.map(a => ({
    ...a,
    base64: `${a.base64.substring(0, 50)}... (${a.base64.length} chars)`
  }))
});

const response = await fetch('/api/v1/chat', { ... });
```

### Check Backend Logs
After sending, check backend logs for:
```
🎨 Routing to Gemma model in LM Studio with 1 image(s)
🎨 Model: google/gemma-3-12b
  📷 Image 1: photo.jpg (image/jpeg)
✅ Gemma response received
```

---

## Complete Working Example (Copy & Paste)

```html
<!DOCTYPE html>
<html>
<head>
  <title>Image Chat Test</title>
</head>
<body>
  <input type="file" id="imageInput" accept="image/*" multiple>
  <input type="text" id="messageInput" placeholder="Your message...">
  <button id="sendButton">Send</button>
  <div id="response"></div>

  <script>
    const API_URL = 'http://localhost:8000/api/v1/chat';
    const TOKEN = 'your-auth-token-here';
    const USER_ID = 1;

    const fileToBase64 = (file) => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.onerror = reject;
      });
    };

    document.getElementById('sendButton').addEventListener('click', async () => {
      const files = Array.from(document.getElementById('imageInput').files);
      const message = document.getElementById('messageInput').value;
      
      if (files.length === 0 && !message) {
        alert('Please select an image or enter a message');
        return;
      }

      const attachments = await Promise.all(
        files.map(async (file) => ({
          type: "image",
          mime: file.type,
          base64: await fileToBase64(file),
          filename: file.name
        }))
      );

      const payload = {
        message: message || "",
        user_id: USER_ID,
        attachments: attachments
      };

      try {
        const response = await fetch(API_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${TOKEN}`
          },
          body: JSON.stringify(payload)
        });

        const result = await response.json();
        
        document.getElementById('response').innerHTML = `
          <h3>Response:</h3>
          <p>${result.message}</p>
          ${result.vision_processed ? `
            <div style="background: #e3f2fd; padding: 10px; margin-top: 10px;">
              ✨ Vision Processed: ${result.model_used}<br>
              📷 Images: ${result.images_count}<br>
              📁 Files: ${result.image_filenames.join(', ')}
            </div>
          ` : ''}
        `;
        
        console.log('Full response:', result);
        
      } catch (error) {
        console.error('Error:', error);
        alert('Failed to send message');
      }
    });
  </script>
</body>
</html>
```

---

## Summary

✅ **What Frontend Sends:**
- `message`: Text prompt (can be empty)
- `attachments`: Array of objects with `type`/`mime`, `base64`, `filename`

✅ **What Frontend Receives:**
- `message`: AI response
- `vision_processed`: Boolean indicating if vision was used
- `model_used`: Which model processed the request
- `images_count`: Number of images processed
- `image_filenames`: List of processed image filenames

✅ **Supported Formats:**
- JPEG, PNG, GIF, WebP, BMP
- Base64 encoded (no data URL prefix needed)
- Single or multiple images per request

---

**Ready to test!** 🚀















