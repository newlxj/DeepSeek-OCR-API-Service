# DeepSeek OCR2 API 服务

DeepSeek-OCR-2 的 RESTful API 服务，支持将 PDF 和图片转换为 Markdown 格式。

[中文文档](./README_CN.md) | [English](./README.md)

## 特性

- **延迟加载模型** - 仅在首次 API 调用时加载模型，启动时节省 GPU 内存
- **同步/异步处理** - 支持同步和异步两种处理模式
- **FIFO 任务队列** - 先进先出队列管理异步任务
- **回调通知** - 异步任务完成后通过 HTTP 回调通知
- **批量处理** - 高效批量处理多张图片
- **PDF 支持** - 直接将 PDF 转换为 Markdown

## 安装
download the [vllm-0.8.5 whl](https://github.com/vllm-project/vllm/releases/tag/v0.8.5)
```bash
# 安装依赖
conda create -n deepseek-ocr2 python=3.12.9 -y
conda activate deepseek-ocr2
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu118
或国内：
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

pip install vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl
pip install -r requirements_api.txt
pip install flash-attn==2.7.3 --no-build-isolation
```

## 配置
模型下载位置：
https://huggingface.co/deepseek-ai/DeepSeek-OCR-2

或国内：
https://modelscope.cn/models/deepseek-ai/DeepSeek-OCR-2
编辑 `config.py` 设置模型路径：


```python
MODEL_PATH = '/your/model/path/deepseek-ocr2'
```

## 快速开始

```bash
# 启动 API 服务
python start_api.py

# 或直接使用 uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 1
```

## API 接口

| 路由 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 健康检查 |
| `/ocr/pdf` | POST | PDF 转 Markdown |
| `/ocr/image` | POST | 单张图片转 Markdown |
| `/ocr/images` | POST | 批量图片转 Markdown |
| `/task/{task_id}` | GET | 查询任务状态 |
| `/queue/status` | GET | 队列状态 |

## 使用示例

### 1. 同步 PDF 转 Markdown

```bash
curl -X POST "http://localhost:8000/ocr/pdf" \
  -F "file=@document.pdf" \
  -F "biz_id=test123" \
  -F "is_async=false" \
  -F "det=false"
```

**响应：**
```json
{
  "code": 200,
  "filename": "document.pdf",
  "taskid": "550e8400-e29b-41d4-a716-446655440000",
  "bizId": "test123",
  "pages": ["# 内容\n\n第一页内容...", "..."]
}
```

### 2. 异步图片转 Markdown

```bash
curl -X POST "http://localhost:8000/ocr/image" \
  -F "file=@page.jpg" \
  -F "biz_id=test123" \
  -F "is_async=true" \
  -F "callback_url=http://your-server.com/callback" \
  -F "det=false"
```

**响应：**
```json
{
  "code": 220,
  "filename": "page.jpg",
  "taskid": "550e8400-e29b-41d4-a716-446655440000",
  "bizId": "test123"
}
```

### 3. 批量图片处理

```bash
curl -X POST "http://localhost:8000/ocr/images" \
  -F "files=@page1.jpg" \
  -F "files=@page2.jpg" \
  -F "files=@page3.jpg" \
  -F "biz_id=test123" \
  -F "is_async=false" \
  -F "det=true"
```

### 4. 查询任务状态

```bash
curl "http://localhost:8000/task/550e8400-e29b-41d4-a716-446655440000"
```

**响应：**
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

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` / `files` | File | 是 | PDF 或图片文件 |
| `biz_id` | string | 是 | 业务 ID，用于追踪 |
| `is_async` | boolean | 否 | 是否异步处理（默认：false） |
| `callback_url` | string | 否* | 回调地址（异步模式必填） |
| `det` | boolean | 否 | 是否输出检测位置信息（默认：false） |
| `skip_pages` | string | 否 | 跳过页码，逗号分隔（仅 PDF） |
| `limit_pages` | int | 否 | 限制处理页数（仅 PDF） |

*`is_async=true` 时必填

## 响应状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功（同步模式） |
| 220 | 任务已接受（异步模式） |
| 400 | 请求参数错误 |
| 404 | 任务不存在 |
| 422 | 文件处理错误 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 / 队列已满 |

## Python 客户端示例

```python
import requests

# 同步图片 OCR
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

# 异步 PDF OCR
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

## 交互式 API 文档

启动服务后访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 项目结构

```
api/
├── main.py                 # FastAPI 应用入口
├── config.py               # API 服务配置
├── exceptions.py           # 自定义异常
├── models/                 # 数据模型
│   ├── requests.py         # 请求模型
│   └── responses.py        # 响应模型
├── routes/                 # 路由
│   ├── ocr.py              # OCR 接口
│   └── health.py           # 健康检查
├── services/               # 业务逻辑
│   ├── model_manager.py    # 模型管理（延迟加载）
│   ├── ocr_service.py      # OCR 处理
│   ├── task_queue.py       # 任务队列
│   └── callback_service.py # 回调服务
└── utils/                  # 工具函数
    └── file_utils.py       # 文件处理
```

## 许可证

MIT License
