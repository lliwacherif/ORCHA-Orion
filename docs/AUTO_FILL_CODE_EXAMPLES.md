# Auto-Fill API - Code Examples

Quick reference with ready-to-use code examples in multiple programming languages.

---

## Python

### Simple Example

```python
import requests
import json

def extract_fields_from_document(file_path, fields):
    """
    Extract specific fields from a document using ORCHA Auto-Fill API.
    
    Args:
        file_path: Path to document (PDF or image)
        fields: List of field definitions
        
    Returns:
        dict with extraction results
    """
    url = "http://your-server.com/api/v1/orcha/auto-fill"
    
    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {"fields": json.dumps(fields)}
        
        response = requests.put(url, files=files, data=data, timeout=60)
        return response.json()

# Example usage
fields = [
    {"field_name": "firstname", "field_type": "string"},
    {"field_name": "lastname", "field_type": "string"},
    {"field_name": "birth_date", "field_type": "date"}
]

result = extract_fields_from_document("id_card.pdf", fields)

if result["success"] and result["message"] == "success":
    print("Extracted data:", result["data"])
else:
    print("Failed:", result["message"])
```

### Advanced Example with Error Handling

```python
import requests
import json
from typing import Dict, List, Optional

class AutoFillClient:
    def __init__(self, api_url: str):
        self.api_url = api_url
    
    def extract_fields(
        self, 
        file_path: str, 
        fields: List[Dict],
        timeout: int = 60
    ) -> Dict:
        """
        Extract fields from document with comprehensive error handling.
        """
        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path, f)}
                data = {"fields": json.dumps(fields)}
                
                response = requests.put(
                    self.api_url, 
                    files=files, 
                    data=data, 
                    timeout=timeout
                )
                response.raise_for_status()
                
                return {
                    "success": True,
                    "result": response.json()
                }
                
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Cannot connect to API server"
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": f"Request timed out after {timeout} seconds"
            }
        except requests.exceptions.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP error: {e}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def extract_identity_fields(self, file_path: str) -> Dict:
        """Convenience method for common identity document fields."""
        fields = [
            {"field_name": "firstname", "field_type": "string"},
            {"field_name": "lastname", "field_type": "string"},
            {"field_name": "birth_date", "field_type": "date"},
            {"field_name": "nationality", "field_type": "string"},
            {"field_name": "document_number", "field_type": "string"}
        ]
        return self.extract_fields(file_path, fields)

# Usage
client = AutoFillClient("http://localhost:8000/api/v1/orcha/auto-fill")
result = client.extract_identity_fields("passport.pdf")

if result["success"]:
    api_response = result["result"]
    if api_response["message"] == "success":
        print("Extracted:", api_response["data"])
    else:
        print("Document invalid:", api_response["message"])
else:
    print("Error:", result["error"])
```

---

## JavaScript/Node.js

### Using Fetch (Browser)

```javascript
async function extractFieldsFromDocument(fileInput, fields) {
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('fields', JSON.stringify(fields));
    
    try {
        const response = await fetch('http://your-server.com/api/v1/orcha/auto-fill', {
            method: 'PUT',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success && result.message === 'success') {
            console.log('Extracted data:', result.data);
            return result.data;
        } else {
            console.error('Extraction failed:', result.message);
            return null;
        }
    } catch (error) {
        console.error('Error:', error);
        return null;
    }
}

// Example usage in HTML
// <input type="file" id="documentFile" />
// <button onclick="handleExtraction()">Extract</button>

function handleExtraction() {
    const fileInput = document.getElementById('documentFile');
    const fields = [
        { field_name: 'firstname', field_type: 'string' },
        { field_name: 'lastname', field_type: 'string' },
        { field_name: 'birth_date', field_type: 'date' }
    ];
    
    extractFieldsFromDocument(fileInput, fields);
}
```

### Using Axios (Node.js)

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

async function extractFields(filePath, fields) {
    const formData = new FormData();
    formData.append('file', fs.createReadStream(filePath));
    formData.append('fields', JSON.stringify(fields));
    
    try {
        const response = await axios.put(
            'http://your-server.com/api/v1/orcha/auto-fill',
            formData,
            {
                headers: formData.getHeaders(),
                timeout: 60000
            }
        );
        
        return {
            success: true,
            data: response.data
        };
    } catch (error) {
        return {
            success: false,
            error: error.message
        };
    }
}

// Example usage
const fields = [
    { field_name: 'firstname', field_type: 'string' },
    { field_name: 'lastname', field_type: 'string' },
    { field_name: 'birth_date', field_type: 'date' }
];

extractFields('./id_card.pdf', fields)
    .then(result => {
        if (result.success) {
            console.log('Extracted:', result.data.data);
        } else {
            console.error('Error:', result.error);
        }
    });
```

---

## PHP

```php
<?php

function extractFieldsFromDocument($filePath, $fields) {
    $url = 'http://your-server.com/api/v1/orcha/auto-fill';
    
    // Prepare multipart form data
    $cfile = new CURLFile($filePath, mime_content_type($filePath), basename($filePath));
    
    $data = [
        'file' => $cfile,
        'fields' => json_encode($fields)
    ];
    
    // Initialize cURL
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'PUT');
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 60);
    
    // Execute request
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    // Parse response
    if ($httpCode === 200) {
        $result = json_decode($response, true);
        return $result;
    } else {
        return [
            'success' => false,
            'message' => 'HTTP error: ' . $httpCode
        ];
    }
}

// Example usage
$fields = [
    ['field_name' => 'firstname', 'field_type' => 'string'],
    ['field_name' => 'lastname', 'field_type' => 'string'],
    ['field_name' => 'birth_date', 'field_type' => 'date']
];

$result = extractFieldsFromDocument('id_card.pdf', $fields);

if ($result['success'] && $result['message'] === 'success') {
    echo "Extracted data:\n";
    print_r($result['data']);
} else {
    echo "Error: " . $result['message'] . "\n";
}

?>
```

---

## Java

```java
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.file.Files;
import org.json.*;

public class AutoFillClient {
    private String apiUrl;
    
    public AutoFillClient(String apiUrl) {
        this.apiUrl = apiUrl;
    }
    
    public JSONObject extractFields(String filePath, JSONArray fields) throws Exception {
        File file = new File(filePath);
        String boundary = "----Boundary" + System.currentTimeMillis();
        
        URL url = new URL(apiUrl);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setDoOutput(true);
        conn.setRequestMethod("PUT");
        conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
        
        try (OutputStream out = conn.getOutputStream();
             PrintWriter writer = new PrintWriter(new OutputStreamWriter(out, "UTF-8"), true)) {
            
            // Add file field
            writer.append("--" + boundary).append("\r\n");
            writer.append("Content-Disposition: form-data; name=\"file\"; filename=\"" + file.getName() + "\"").append("\r\n");
            writer.append("Content-Type: application/octet-stream").append("\r\n\r\n");
            writer.flush();
            
            Files.copy(file.toPath(), out);
            out.flush();
            writer.append("\r\n");
            
            // Add fields parameter
            writer.append("--" + boundary).append("\r\n");
            writer.append("Content-Disposition: form-data; name=\"fields\"").append("\r\n\r\n");
            writer.append(fields.toString()).append("\r\n");
            
            // End boundary
            writer.append("--" + boundary + "--").append("\r\n");
            writer.flush();
        }
        
        // Read response
        int responseCode = conn.getResponseCode();
        if (responseCode == HttpURLConnection.HTTP_OK) {
            BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
            StringBuilder response = new StringBuilder();
            String line;
            
            while ((line = in.readLine()) != null) {
                response.append(line);
            }
            in.close();
            
            return new JSONObject(response.toString());
        } else {
            throw new IOException("HTTP error code: " + responseCode);
        }
    }
    
    public static void main(String[] args) {
        try {
            AutoFillClient client = new AutoFillClient("http://localhost:8000/api/v1/orcha/auto-fill");
            
            // Define fields to extract
            JSONArray fields = new JSONArray();
            fields.put(new JSONObject().put("field_name", "firstname").put("field_type", "string"));
            fields.put(new JSONObject().put("field_name", "lastname").put("field_type", "string"));
            fields.put(new JSONObject().put("field_name", "birth_date").put("field_type", "date"));
            
            // Extract fields
            JSONObject result = client.extractFields("id_card.pdf", fields);
            
            if (result.getBoolean("success") && result.getString("message").equals("success")) {
                System.out.println("Extracted data:");
                System.out.println(result.getJSONObject("data").toString(2));
            } else {
                System.out.println("Error: " + result.getString("message"));
            }
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

---

## C# (.NET)

```csharp
using System;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

public class AutoFillClient
{
    private readonly string apiUrl;
    private readonly HttpClient httpClient;
    
    public AutoFillClient(string apiUrl)
    {
        this.apiUrl = apiUrl;
        this.httpClient = new HttpClient();
        this.httpClient.Timeout = TimeSpan.FromSeconds(60);
    }
    
    public async Task<JsonDocument> ExtractFields(string filePath, object[] fields)
    {
        using var form = new MultipartFormDataContent();
        
        // Add file
        var fileStream = File.OpenRead(filePath);
        var fileContent = new StreamContent(fileStream);
        fileContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue("application/octet-stream");
        form.Add(fileContent, "file", Path.GetFileName(filePath));
        
        // Add fields
        var fieldsJson = JsonSerializer.Serialize(fields);
        form.Add(new StringContent(fieldsJson, Encoding.UTF8, "text/plain"), "fields");
        
        // Send request
        var request = new HttpRequestMessage(HttpMethod.Put, apiUrl)
        {
            Content = form
        };
        
        var response = await httpClient.SendAsync(request);
        response.EnsureSuccessStatusCode();
        
        var responseBody = await response.Content.ReadAsStringAsync();
        return JsonDocument.Parse(responseBody);
    }
    
    public static async Task Main(string[] args)
    {
        var client = new AutoFillClient("http://localhost:8000/api/v1/orcha/auto-fill");
        
        // Define fields
        var fields = new[]
        {
            new { field_name = "firstname", field_type = "string" },
            new { field_name = "lastname", field_type = "string" },
            new { field_name = "birth_date", field_type = "date" }
        };
        
        try
        {
            var result = await client.ExtractFields("id_card.pdf", fields);
            var root = result.RootElement;
            
            if (root.GetProperty("success").GetBoolean() && 
                root.GetProperty("message").GetString() == "success")
            {
                Console.WriteLine("Extracted data:");
                Console.WriteLine(root.GetProperty("data").ToString());
            }
            else
            {
                Console.WriteLine($"Error: {root.GetProperty("message").GetString()}");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Exception: {ex.Message}");
        }
    }
}
```

---

## Ruby

```ruby
require 'net/http'
require 'uri'
require 'json'
require 'mime/types'

class AutoFillClient
  def initialize(api_url)
    @api_url = api_url
  end
  
  def extract_fields(file_path, fields)
    uri = URI.parse(@api_url)
    
    # Prepare multipart form data
    boundary = "----Boundary#{Time.now.to_i}"
    
    # Build request body
    body = []
    
    # Add file
    body << "--#{boundary}\r\n"
    body << "Content-Disposition: form-data; name=\"file\"; filename=\"#{File.basename(file_path)}\"\r\n"
    body << "Content-Type: #{MIME::Types.type_for(file_path).first || 'application/octet-stream'}\r\n\r\n"
    body << File.read(file_path)
    body << "\r\n"
    
    # Add fields
    body << "--#{boundary}\r\n"
    body << "Content-Disposition: form-data; name=\"fields\"\r\n\r\n"
    body << fields.to_json
    body << "\r\n"
    
    # End boundary
    body << "--#{boundary}--\r\n"
    
    # Create request
    request = Net::HTTP::Put.new(uri.path)
    request.body = body.join
    request['Content-Type'] = "multipart/form-data; boundary=#{boundary}"
    
    # Send request
    response = Net::HTTP.start(uri.hostname, uri.port) do |http|
      http.request(request)
    end
    
    JSON.parse(response.body)
  end
end

# Example usage
client = AutoFillClient.new('http://localhost:8000/api/v1/orcha/auto-fill')

fields = [
  { field_name: 'firstname', field_type: 'string' },
  { field_name: 'lastname', field_type: 'string' },
  { field_name: 'birth_date', field_type: 'date' }
]

result = client.extract_fields('id_card.pdf', fields)

if result['success'] && result['message'] == 'success'
  puts 'Extracted data:'
  puts result['data']
else
  puts "Error: #{result['message']}"
end
```

---

## Go

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "mime/multipart"
    "net/http"
    "os"
    "path/filepath"
    "time"
)

type Field struct {
    FieldName string `json:"field_name"`
    FieldType string `json:"field_type"`
}

type AutoFillClient struct {
    apiURL string
    client *http.Client
}

func NewAutoFillClient(apiURL string) *AutoFillClient {
    return &AutoFillClient{
        apiURL: apiURL,
        client: &http.Client{Timeout: 60 * time.Second},
    }
}

func (c *AutoFillClient) ExtractFields(filePath string, fields []Field) (map[string]interface{}, error) {
    // Open file
    file, err := os.Open(filePath)
    if err != nil {
        return nil, err
    }
    defer file.Close()
    
    // Create multipart form
    body := &bytes.Buffer{}
    writer := multipart.NewWriter(body)
    
    // Add file
    part, err := writer.CreateFormFile("file", filepath.Base(filePath))
    if err != nil {
        return nil, err
    }
    _, err = io.Copy(part, file)
    if err != nil {
        return nil, err
    }
    
    // Add fields
    fieldsJSON, err := json.Marshal(fields)
    if err != nil {
        return nil, err
    }
    err = writer.WriteField("fields", string(fieldsJSON))
    if err != nil {
        return nil, err
    }
    
    err = writer.Close()
    if err != nil {
        return nil, err
    }
    
    // Create request
    req, err := http.NewRequest("PUT", c.apiURL, body)
    if err != nil {
        return nil, err
    }
    req.Header.Set("Content-Type", writer.FormDataContentType())
    
    // Send request
    resp, err := c.client.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    // Parse response
    var result map[string]interface{}
    err = json.NewDecoder(resp.Body).Decode(&result)
    if err != nil {
        return nil, err
    }
    
    return result, nil
}

func main() {
    client := NewAutoFillClient("http://localhost:8000/api/v1/orcha/auto-fill")
    
    fields := []Field{
        {FieldName: "firstname", FieldType: "string"},
        {FieldName: "lastname", FieldType: "string"},
        {FieldName: "birth_date", FieldType: "date"},
    }
    
    result, err := client.ExtractFields("id_card.pdf", fields)
    if err != nil {
        fmt.Printf("Error: %v\n", err)
        return
    }
    
    if result["success"].(bool) && result["message"].(string) == "success" {
        fmt.Println("Extracted data:")
        data := result["data"].(map[string]interface{})
        for key, value := range data {
            fmt.Printf("  %s: %v\n", key, value)
        }
    } else {
        fmt.Printf("Error: %s\n", result["message"])
    }
}
```

---

## Quick Testing (cURL)

```bash
# Basic test
curl -X PUT http://localhost:8000/api/v1/orcha/auto-fill \
  -F 'file=@document.pdf' \
  -F 'fields=[{"field_name":"firstname","field_type":"string"},{"field_name":"lastname","field_type":"string"}]'

# Pretty-printed output
curl -X PUT http://localhost:8000/api/v1/orcha/auto-fill \
  -F 'file=@document.pdf' \
  -F 'fields=[{"field_name":"firstname","field_type":"string"}]' | jq '.'

# Save response to file
curl -X PUT http://localhost:8000/api/v1/orcha/auto-fill \
  -F 'file=@document.pdf' \
  -F 'fields=[{"field_name":"firstname","field_type":"string"}]' \
  -o response.json
```

---

## Common Field Definitions

### Identity Documents
```json
[
  {"field_name": "firstname", "field_type": "string"},
  {"field_name": "lastname", "field_type": "string"},
  {"field_name": "birth_date", "field_type": "date"},
  {"field_name": "birth_place", "field_type": "string"},
  {"field_name": "nationality", "field_type": "string"},
  {"field_name": "document_number", "field_type": "string"},
  {"field_name": "expiry_date", "field_type": "date"}
]
```

### Invoices
```json
[
  {"field_name": "invoice_number", "field_type": "string"},
  {"field_name": "invoice_date", "field_type": "date"},
  {"field_name": "total_amount", "field_type": "number"},
  {"field_name": "vendor_name", "field_type": "string"}
]
```

### Contracts
```json
[
  {"field_name": "contract_number", "field_type": "string"},
  {"field_name": "start_date", "field_type": "date"},
  {"field_name": "end_date", "field_type": "date"},
  {"field_name": "party_a", "field_type": "string"},
  {"field_name": "party_b", "field_type": "string"}
]
```

---

## Need Help?

- API Documentation: `docs/AUTO_FILL_API_V2.md`
- Python Test Script: `test_auto_fill_v2.py`
- Full Summary: `REFACTOR_SUMMARY.md`

