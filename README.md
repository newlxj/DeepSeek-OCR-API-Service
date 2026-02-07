# DeepSeek OCR2 API Service

A RESTful API service for DeepSeek-OCR-2 that converts PDFs and images to Markdown format.

[中文文档](./README_CN.md) | [English](./README.md)

## Features

- **Delayed Model Loading** - Model loads only on first API call, saving GPU memory at startup
- **Sync/Async Processing** - Supports both synchronous and asynchronous processing modes
- **FIFO Task Queue** - First-In-First-Out queue for async task management
- **Callback Notifications** - HTTP callbacks when async tasks complete
- **Batch Processing** - Efficient batch processing for multiple images
- **PDF Support** - Direct PDF to Markdown conversion

## Installation

Download the [vllm-0.8.5 whl](https://github.com/vllm-project/vllm/releases/tag/v0.8.5)

```bash
# Create conda environment
conda create -n deepseek-ocr2 python=3.12.9 -y
conda activate deepseek-ocr2

# Install PyTorch
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu118

# Or using China mirror:
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

# Install vLLM
pip install vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl

# Install API dependencies
pip install -r requirements_api.txt

# Install flash attention
pip install flash-attn==2.7.3 --no-build-isolation
```

## Configuration

**Model download:**

- HuggingFace: https://huggingface.co/deepseek-ai/DeepSeek-OCR-2
- ModelScope (China): https://modelscope.cn/models/deepseek-ai/DeepSeek-OCR-2

Edit `config.py` to set your model path:

```python
MODEL_PATH = '/your/model/path/deepseek-ocr2'
```

## Quick Start

```bash
# Start the API server
python start_api.py

# Or use uvicorn directly
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 1
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/ocr/pdf` | POST | PDF to Markdown |
| `/ocr/image` | POST | Single image to Markdown |
| `/ocr/images` | POST | Batch images to Markdown |
| `/task/{task_id}` | GET | Query task status |
| `/queue/status` | GET | Queue status |

## Examples

### 1. Sync PDF to Markdown

```bash
curl -X POST "http://localhost:8000/ocr/pdf" \
  -F "file=@document.pdf" \
  -F "biz_id=test123" \
  -F "is_async=false" \
  -F "det=false"
```

**Response:**
```json
{
  "code": 200,
  "filename": "document.pdf",
  "taskid": "550e8400-e29b-41d4-a716-446655440000",
  "bizId": "test123",
  "pages": ["# Content\n\nPage 1 content...", "..."]
}
```

### 2. Async Image to Markdown

```bash
curl -X POST "http://localhost:8000/ocr/image" \
  -F "file=@page.jpg" \
  -F "biz_id=test123" \
  -F "is_async=true" \
  -F "callback_url=http://your-server.com/callback" \
  -F "det=false"
```

**Response:**
```json
{
  "code": 220,
  "filename": "page.jpg",
  "taskid": "550e8400-e29b-41d4-a716-446655440000",
  "bizId": "test123"
}
```

### 3. Batch Images Processing

```bash
curl -X POST "http://localhost:8000/ocr/images" \
  -F "files=@page1.jpg" \
  -F "files=@page2.jpg" \
  -F "files=@page3.jpg" \
  -F "biz_id=test123" \
  -F "is_async=false" \
  -F "det=true"
```

### 4. Query Task Status

```bash
curl "http://localhost:8000/task/550e8400-e29b-41d4-a716-446655440000"
```

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "biz_id": "test123",
  "filename": "document.pdf",
  "status": "completed",
  "created_at": 1234567890.123,
  "completed_at": 1234567900.456,
  "result": null
}
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` / `files` | File | Yes | PDF or image file(s) |
| `biz_id` | string | Yes | Business ID for tracking |
| `is_async` | boolean | No | Async mode (default: false) |
| `callback_url` | string | No* | Callback URL (required for async) |
| `det` | boolean | No | Include detection info (default: false) |
| `skip_pages` | string | No | Skip pages (comma-separated, PDF only) |
| `limit_pages` | int | No | Limit page count (PDF only) |

*Required when `is_async=true`

## Response Codes

| Code | Description |
|------|-------------|
| 200 | Success (sync mode) |
| 220 | Task accepted (async mode) |
| 400 | Bad request |
| 404 | Task not found |
| 422 | File processing error |
| 500 | Internal server error |
| 503 | Service unavailable / Queue full |

## Python Client Example

```python
import requests

# Sync image OCR
def ocr_image(image_path: str) -> dict:
    url = "http://localhost:8000/ocr/image"
    files = {"file": open(image_path, "rb")}
    data = {
        "biz_id": "test123",
        "is_async": False,
        "det": False
    }
    response = requests.post(url, files=files, data=data)
    return response.json()

# Async PDF OCR
def ocr_pdf_async(pdf_path: str, callback_url: str) -> dict:
    url = "http://localhost:8000/ocr/pdf"
    files = {"file": open(pdf_path, "rb")}
    data = {
        "biz_id": "test123",
        "is_async": True,
        "callback_url": callback_url,
        "det": False
    }
    response = requests.post(url, files=files, data=data)
    return response.json()
```

## Interactive API Documentation

Start the server and visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
api/
├── main.py                 # FastAPI application entry
├── config.py               # API service configuration
├── exceptions.py           # Custom exceptions
├── models/                 # Data models
│   ├── requests.py         # Request models
│   └── responses.py        # Response models
├── routes/                 # API routes
│   ├── ocr.py              # OCR endpoints
│   └── health.py           # Health check endpoints
├── services/               # Business logic
│   ├── model_manager.py    # Model manager (lazy loading)
│   ├── ocr_service.py      # OCR processing service
│   ├── task_queue.py       # Task queue management
│   └── callback_service.py # Callback service
└── utils/                  # Utilities
    └── file_utils.py       # File processing utilities
```

## License

MIT License
