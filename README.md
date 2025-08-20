# Simple RAG Assistant

一个精简的 RAG (Retrieval-Augmented Generation) 助手，支持基本的问答功能。

## 功能特性

- 🔐 JWT 认证
- 🔍 RAG 问答 (支持 Ollama 本地 LLM)
- 📄 PDF 文档上传和处理
- 📊 Prometheus 指标
- 🚀 FastAPI 后端
- 💾 Qdrant 向量存储 (可选)
- 🦙 Ollama 自托管 LLM 服务

## 快速开始

### 1. 安装 Ollama
```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# 启动 Ollama 服务
ollama serve

# 下载模型
ollama pull llama3.2:latest
ollama pull nomic-embed-text
```

### 2. 安装 Python 依赖
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 3. 配置环境变量
```bash
# 编辑 .env 文件，设置 Ollama 配置
# 主要配置项：
# - OLLAMA_BASE_URL=http://localhost:11434
# - MODEL_NAME=llama3.2:latest
# - EMBED_MODEL=nomic-embed-text
```

### 4. 启动服务
```bash
python run.py
```

### 5. 测试 API
- 健康检查: GET /api/v1/health
- 登录: POST /api/v1/login
- 问答: POST /api/v1/query
- 文档上传: POST /api/v1/upload
- 文档列表: GET /api/v1/documents
- 统计信息: GET /api/v1/stats/{kb_id}
- 清空知识库: DELETE /api/v1/knowledge-base/{kb_id}
- API 文档: GET /docs

## 项目结构
```
.
├── backend/                    # 后端代码
│   ├── app/                   # 应用代码
│   │   ├── services/          # 核心服务
│   │   ├── auth.py           # 认证
│   │   ├── config.py         # 配置
│   │   └── main.py           # 主应用
│   └── requirements.txt      # Python 依赖
├── samples/                   # PDF 样本文件
├── .env                      # 环境变量配置
├── run.py                    # 启动脚本
└── README.md                 # 项目说明
```

## 使用说明

### 上传 PDF 文档
```bash
# 登录获取 token
curl -X POST "http://localhost:8000/api/v1/login" \
  -F "username=testuser"

# 上传 PDF
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@your_document.pdf" \
  -F "kb_id=test" \
  -F "title=文档标题"
```

### RAG 问答查询
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"kb_id":"test","query":"你的问题","top_k":3}'
```

### 查看文档列表
```bash
curl -X GET "http://localhost:8000/api/v1/documents?kb_id=test" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 清空知识库
```bash
curl -X DELETE "http://localhost:8000/api/v1/knowledge-base/test" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 技术架构

- **后端框架**: FastAPI
- **LLM 服务**: Ollama (本地部署)
- **向量数据库**: Qdrant
- **认证**: JWT
- **监控**: Prometheus 指标

## 注意事项

- 确保 Ollama 服务正在运行
- 确保 Qdrant 数据库可访问
- 首次使用需要下载模型文件
- 支持 PDF 文档格式
- 所有数据本地存储，保护隐私
