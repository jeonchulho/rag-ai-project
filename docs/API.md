# API Documentation

## Base URL

```
http://localhost/api/v1
```

## Authentication

Currently, no authentication is required. Future versions will implement JWT-based authentication.

## Common Headers

```
Content-Type: application/json
X-Request-ID: <unique-request-id>
```

## Error Responses

All endpoints may return these error codes:

- `400`: Bad Request - Invalid input
- `404`: Not Found - Resource not found
- `422`: Validation Error - Pydantic validation failed
- `429`: Too Many Requests - Rate limit exceeded
- `500`: Internal Server Error - Server error
- `503`: Service Unavailable - Service temporarily unavailable

Error response format:
```json
{
  "detail": "Error message"
}
```

---

## Health Check Endpoints

### GET /health

Overall system health check.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "instance_id": "1",
  "timestamp": "2024-01-11T10:00:00Z",
  "services": [
    {
      "name": "Redis",
      "status": "healthy",
      "response_time": 5.2
    }
  ]
}
```

### GET /health/services

Individual service health status.

**Response** (200 OK):
```json
[
  {
    "name": "Redis",
    "status": "healthy",
    "response_time": 5.2,
    "details": null
  },
  {
    "name": "PostgreSQL",
    "status": "healthy",
    "response_time": 10.5
  }
]
```

---

## Search Endpoints

### POST /search

Basic search across text, images, or documents.

**Request Body**:
```json
{
  "query": "artificial intelligence papers",
  "search_type": "text",
  "top_k": 5,
  "filters": {}
}
```

**Parameters**:
- `query` (string, required): Search query text
- `search_type` (enum, optional): `text`, `image`, `document`, or `all` (default: `all`)
- `top_k` (integer, optional): Number of results (1-50, default: 5)
- `filters` (object, optional): Additional metadata filters

**Response** (200 OK):
```json
{
  "results": [
    {
      "id": "doc-123",
      "content": "AI is transforming...",
      "score": 0.95,
      "metadata": {
        "filename": "ai-paper.pdf"
      },
      "document_type": "text"
    }
  ],
  "total": 1,
  "query": "artificial intelligence papers",
  "search_type": "text",
  "execution_time": 0.234
}
```

### POST /search/natural

Natural language query processing with intent detection and action scheduling.

**Request Body**:
```json
{
  "query": "Search AI papers, summarize them, and email the summary to hong@example.com at 10 AM",
  "context": {}
}
```

**Parameters**:
- `query` (string, required): Natural language query
- `context` (object, optional): Additional context

**Response** (200 OK):
```json
{
  "intent": "search_summarize_email",
  "entities": {
    "emails": ["hong@example.com"],
    "times": ["10 AM"],
    "keywords": "AI papers"
  },
  "search_results": [
    {
      "id": "doc-123",
      "content": "AI paper content...",
      "score": 0.95,
      "metadata": {},
      "document_type": "text"
    }
  ],
  "summary": "Summary of AI papers...",
  "scheduled_actions": [
    {
      "action_type": "email",
      "parameters": {
        "to": "hong@example.com",
        "subject": "Search Results Summary",
        "body": "Summary of AI papers..."
      },
      "scheduled_time": "2024-01-12T10:00:00Z"
    }
  ],
  "response_text": "Found 5 relevant results. Generated summary of the results. Scheduled 1 action(s).",
  "execution_time": 2.456
}
```

### GET /search/similar/{document_id}

Find similar documents based on a reference document.

**Parameters**:
- `document_id` (path, required): Reference document ID
- `top_k` (query, optional): Number of results (default: 5)

**Response** (200 OK):
```json
{
  "results": [
    {
      "id": "doc-456",
      "content": "Similar content...",
      "score": 0.89,
      "metadata": {},
      "document_type": "text"
    }
  ],
  "total": 1,
  "query": "similar_to:doc-123",
  "search_type": "similarity",
  "execution_time": 0.156
}
```

---

## Upload Endpoints

### POST /upload/text

Upload a text document.

**Request**: multipart/form-data
- `file` (file, required): Text file

**Response** (200 OK):
```json
{
  "document_id": "uuid-123",
  "filename": "document.txt",
  "file_size": 1024,
  "content_type": "text/plain",
  "status": "success",
  "message": "Text document uploaded and indexed successfully"
}
```

### POST /upload/image

Upload an image.

**Request**: multipart/form-data
- `file` (file, required): Image file
- `description` (form, optional): Image description

**Response** (200 OK):
```json
{
  "document_id": "uuid-456",
  "filename": "image.jpg",
  "file_size": 204800,
  "content_type": "image/jpeg",
  "status": "success",
  "message": "Image uploaded and indexed successfully"
}
```

### POST /upload/document

Upload a PDF or DOCX document.

**Request**: multipart/form-data
- `file` (file, required): PDF or DOCX file

**Response** (200 OK):
```json
{
  "document_id": "uuid-789",
  "filename": "report.pdf",
  "file_size": 512000,
  "content_type": "application/pdf",
  "status": "success",
  "message": "Document uploaded and indexed successfully"
}
```

---

## Action Endpoints

### POST /action/email

Schedule an email to be sent.

**Request Body**:
```json
{
  "action_type": "email",
  "parameters": {
    "to": "recipient@example.com",
    "subject": "Email Subject",
    "body": "Email body content"
  },
  "scheduled_time": "2024-01-12T10:00:00Z"
}
```

**Parameters**:
- `action_type` (enum, required): Must be `email`
- `parameters` (object, required): Email parameters
  - `to` (email, required): Recipient email
  - `subject` (string, required): Email subject
  - `body` (string, required): Email body
- `scheduled_time` (datetime, optional): When to send (ISO 8601 format)

**Response** (200 OK):
```json
{
  "task_id": "celery-task-123",
  "action_type": "email",
  "status": "scheduled",
  "scheduled_time": "2024-01-12T10:00:00Z",
  "message": "Email task scheduled successfully"
}
```

### POST /action/summarize

Schedule content summarization.

**Request Body**:
```json
{
  "action_type": "summarize",
  "parameters": {
    "content": "Long text content to summarize...",
    "max_length": 500
  }
}
```

**Response** (200 OK):
```json
{
  "task_id": "celery-task-456",
  "action_type": "summarize",
  "status": "pending",
  "scheduled_time": null,
  "message": "Summarization task scheduled successfully"
}
```

### GET /action/status/{task_id}

Get status of a background task.

**Parameters**:
- `task_id` (path, required): Task ID

**Response** (200 OK):
```json
{
  "task_id": "celery-task-123",
  "status": "completed",
  "result": {
    "status": "success",
    "message": "Email sent to recipient@example.com"
  },
  "error": null,
  "created_at": "2024-01-11T10:00:00Z",
  "updated_at": "2024-01-11T10:05:00Z"
}
```

**Task Statuses**:
- `pending`: Task is queued
- `running`: Task is executing
- `completed`: Task finished successfully
- `failed`: Task failed with error
- `retrying`: Task is retrying after failure
- `cancelled`: Task was cancelled

---

## Rate Limiting

Rate limits are enforced at the Nginx level:
- **100 requests/second** per IP address
- Burst of 20 additional requests allowed
- Exceeding limit returns `429 Too Many Requests`

---

## Pagination

Currently, pagination is handled through the `top_k` parameter. Future versions will implement cursor-based pagination.

---

## Interactive Documentation

After starting the system, access interactive API documentation:
- **Swagger UI**: http://localhost/docs
- **ReDoc**: http://localhost/redoc
- **OpenAPI Spec**: http://localhost/openapi.json

---

## Code Examples

### Python

```python
import requests

# Search for documents
response = requests.post(
    "http://localhost/api/v1/search",
    json={
        "query": "machine learning",
        "search_type": "text",
        "top_k": 10
    }
)
results = response.json()

# Upload a document
with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost/api/v1/upload/document",
        files={"file": f}
    )
upload_result = response.json()

# Schedule an email
response = requests.post(
    "http://localhost/api/v1/action/email",
    json={
        "action_type": "email",
        "parameters": {
            "to": "user@example.com",
            "subject": "Test",
            "body": "Hello!"
        }
    }
)
task = response.json()
```

### cURL

```bash
# Health check
curl http://localhost/api/v1/health

# Search
curl -X POST http://localhost/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "AI research",
    "search_type": "all",
    "top_k": 5
  }'

# Natural language query
curl -X POST http://localhost/api/v1/search/natural \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Search papers and email to me@example.com"
  }'

# Upload text file
curl -X POST http://localhost/api/v1/upload/text \
  -F "file=@document.txt"
```

### JavaScript

```javascript
// Search for documents
const searchResults = await fetch('http://localhost/api/v1/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'artificial intelligence',
    search_type: 'text',
    top_k: 5
  })
}).then(res => res.json());

// Upload an image
const formData = new FormData();
formData.append('file', imageFile);
const uploadResult = await fetch('http://localhost/api/v1/upload/image', {
  method: 'POST',
  body: formData
}).then(res => res.json());
```

---

## WebSocket Support (Planned)

Future versions will support WebSocket connections for:
- Real-time search result streaming
- Progress updates for long-running tasks
- Live notifications

---

## Versioning

The API is versioned through the URL path (`/api/v1`). Future versions will maintain backward compatibility where possible.

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/jeonchulho/rag-ai-project/issues
- Documentation: https://github.com/jeonchulho/rag-ai-project/docs
