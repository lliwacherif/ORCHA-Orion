# Smart Attachment Processing with RAG

## Overview

ORCHA now **intelligently processes file attachments** and automatically uses RAG to answer questions about them!

## How It Works

### The Smart Flow:

```
User sends message + PDF attachment
         ↓
ORCHA detects attachment
         ↓
Step 1: Extract text (OCR)
         ↓
Step 2: Ingest into RAG database
         ↓
Step 3: Query RAG for relevant context
         ↓
Step 4: LLM answers using context from the PDF
         ↓
Response with answer + sources
```

### All in ONE request! 🎉

## Usage Example

### Request:
```json
POST /api/v1/orcha/chat

{
  "user_id": "user123",
  "message": "What is the vacation policy in this document?",
  "attachments": [
    {
      "uri": "/path/to/company-handbook.pdf",
      "type": "application/pdf"
    }
  ]
}
```

### Response:
```json
{
  "status": "ok",
  "message": "According to the company handbook, employees receive 15 days of vacation per year...",
  "contexts": [
    {
      "source": "attachment_user123",
      "text": "Vacation Policy: All full-time employees are entitled to 15 days...",
      "score": 0.95
    }
  ],
  "attachments_processed": 1,
  "ingested_documents": 1,
  "model_response": {...}
}
```

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | "ok" or "error" |
| `message` | string | AI's answer (display this in UI) |
| `contexts` | array | RAG sources used (from the PDF) |
| `attachments_processed` | int | Number of files processed |
| `ingested_documents` | int | Number successfully added to RAG |
| `model_response` | object | Full LM Studio response (debug) |

## React Integration

### Simple Chat with PDF:

```jsx
const sendMessageWithPDF = async (message, pdfFile) => {
  // Step 1: Upload PDF to your storage (get URI)
  const fileUri = await uploadFile(pdfFile);
  
  // Step 2: Send to ORCHA
  const response = await fetch('http://localhost:8000/api/v1/orcha/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: 'user123',
      message: message,
      attachments: [
        {
          uri: fileUri,
          type: pdfFile.type
        }
      ]
    })
  });
  
  const data = await response.json();
  
  if (data.status === 'ok') {
    // Display the AI's answer
    console.log('Answer:', data.message);
    
    // Show which document was used
    if (data.contexts) {
      console.log('Sources:', data.contexts.map(c => c.source));
    }
    
    // Show processing stats
    console.log(`Processed ${data.attachments_processed} file(s)`);
  }
};
```

### Complete React Component:

```jsx
import { useState } from 'react';

const SmartChatWithAttachments = () => {
  const [message, setMessage] = useState('');
  const [file, setFile] = useState(null);
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const sendMessage = async () => {
    setLoading(true);
    
    try {
      // Build request
      const payload = {
        user_id: 'user123',
        message: message
      };
      
      // Add attachment if file selected
      if (file) {
        // In real app: upload file first and get URI
        payload.attachments = [{
          uri: `/uploads/${file.name}`,
          type: file.type
        }];
      }
      
      const res = await fetch('http://localhost:8000/api/v1/orcha/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      const data = await res.json();
      setResponse(data);
      
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <h2>Smart Chat with PDF</h2>
      
      {/* File upload */}
      <div className="file-input">
        <input 
          type="file" 
          accept=".pdf,.png,.jpg,.jpeg"
          onChange={handleFileChange}
        />
        {file && <span>📄 {file.name}</span>}
      </div>
      
      {/* Message input */}
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Ask a question about the document..."
      />
      
      <button onClick={sendMessage} disabled={loading}>
        {loading ? 'Processing...' : 'Send'}
      </button>
      
      {/* Response */}
      {response && response.status === 'ok' && (
        <div className="response">
          <div className="message">
            <strong>Answer:</strong>
            <p>{response.message}</p>
          </div>
          
          {/* Show sources */}
          {response.contexts && (
            <div className="sources">
              <strong>Sources from document:</strong>
              {response.contexts.map((ctx, i) => (
                <div key={i} className="source-item">
                  <span className="score">Score: {ctx.score}</span>
                  <p>{ctx.text?.substring(0, 200)}...</p>
                </div>
              ))}
            </div>
          )}
          
          {/* Processing info */}
          {response.attachments_processed > 0 && (
            <div className="info">
              ✅ Processed {response.attachments_processed} file(s)
              and added {response.ingested_documents} to knowledge base
            </div>
          )}
        </div>
      )}
      
      {response && response.status === 'error' && (
        <div className="error">
          ❌ Error: {response.error}
        </div>
      )}
    </div>
  );
};

export default SmartChatWithAttachments;
```

## Supported File Types

The OCR service supports:
- **PDF** (.pdf)
- **Images** (.png, .jpg, .jpeg, .bmp, .tiff)
- **Scanned documents**

## Processing Time

Depending on file size:
- Small PDFs (< 5 pages): 5-15 seconds
- Medium PDFs (5-20 pages): 15-45 seconds
- Large PDFs (> 20 pages): 45+ seconds

**Pro tip:** Show a loading indicator in your UI!

## Multiple Attachments

You can send multiple files at once:

```json
{
  "user_id": "user123",
  "message": "Compare these two documents",
  "attachments": [
    {"uri": "/path/to/doc1.pdf", "type": "application/pdf"},
    {"uri": "/path/to/doc2.pdf", "type": "application/pdf"}
  ]
}
```

ORCHA will:
1. Process both documents
2. Ingest both into RAG
3. Query both for relevant context
4. LLM answers using information from both

## Error Handling

If attachment processing fails:

```json
{
  "status": "error",
  "error": "OCR service unavailable",
  "message": null
}
```

**Important:** Individual attachment failures won't stop the whole request. If 1 of 3 files fails, the other 2 will still be processed.

## Use Cases

### 1. Contract Analysis
```javascript
"What are the payment terms in this contract?"
// Attach: contract.pdf
```

### 2. Invoice Processing
```javascript
"Extract all line items from this invoice"
// Attach: invoice.pdf
```

### 3. Document Q&A
```javascript
"Summarize the key points in this report"
// Attach: annual-report.pdf
```

### 4. Multi-document Search
```javascript
"Find all mentions of 'compliance' in these documents"
// Attach: multiple PDFs
```

## Requirements

Make sure these services are running:

1. ✅ **ORCHA** - `http://localhost:8000`
2. ✅ **LM Studio** - `http://192.168.1.37:1234` (with model loaded)
3. ✅ **OCR Service** - `http://localhost:8001`
4. ✅ **RAG Service** - `http://localhost:8002`

## Benefits Over Old Approach

### Old Way (Manual):
1. Send PDF to `/orcha/ocr` → Get job ID
2. Poll for OCR completion
3. Send text to `/orcha/ingest` → Wait
4. Send question to `/orcha/chat` with `use_rag=true`

### New Way (Automatic):
1. Send PDF + question to `/orcha/chat` → Get answer ✨

**4 steps reduced to 1!** 🎉

## Notes

- Documents are **automatically added to your RAG database** when attached
- Future queries (even without attachments) can access previously uploaded documents
- To query previously uploaded docs: just send `use_rag=true` without attachments
- Each user's documents are tagged with their `user_id` in metadata

---

**Your PDF-powered AI assistant is ready! 🚀**

