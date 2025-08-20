📁 PDF 样本文件目录

将你的 PDF 文件放在这个目录下，然后使用以下方式上传：

## 🚀 使用方法

### 1. 通过 API 上传
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

### 2. 通过测试脚本
```bash
python test_pdf_upload.py
```

### 3. 通过 Web 界面
访问 http://localhost:8000/docs 查看 Swagger UI

## 📋 支持的文件格式
- PDF (.pdf)

## 🔧 配置说明
- kb_id: 知识库 ID，用于组织文档
- title: 文档标题（可选）
- 文件会自动分块并生成向量嵌入

## 📊 处理流程
1. 上传 PDF 文件
2. 提取文本内容
3. 分块处理（1000字符/块，200字符重叠）
4. 生成向量嵌入
5. 存储到 Qdrant 向量数据库
6. 可用于 RAG 问答查询
