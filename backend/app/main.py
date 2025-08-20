from fastapi import FastAPI, Depends, HTTPException, Response, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.auth import get_current_subject, create_access_token
from app.services.rag import rag_answer
from app.services.pdf_processor import pdf_processor
import os
import tempfile
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST


class QueryRequest(BaseModel):
    kb_id: str
    query: str
    top_k: int = 5


app = FastAPI(title="RAG Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "RAG Assistant API", "docs": "/docs"}


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/login")
def login(username: str = Form(...)):
    return {"access_token": create_access_token(username)}


@app.post("/api/v1/query")
async def query(body: QueryRequest, sub: str = Depends(get_current_subject)):
    result = await rag_answer(kb_id=body.kb_id, query=body.query, top_k=body.top_k)
    return result


@app.post("/api/v1/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    kb_id: str = Form(...),
    title: str = Form(None),
    sub: str = Depends(get_current_subject)
):
    """上传并处理 PDF 文件"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")
    
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # 处理 PDF
        result = await pdf_processor.process_pdf(
            file_path=temp_file_path,
            kb_id=kb_id,
            title=title or file.filename
        )
        
        # 清理临时文件
        os.unlink(temp_file_path)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")


@app.get("/api/v1/documents")
async def list_documents(kb_id: str, sub: str = Depends(get_current_subject)):
    """列出知识库中的文档"""
    try:
        from app.services.vector_store import vector_store
        
        # 获取文档列表
        documents = vector_store.get_documents(kb_id)
        
        # 获取统计信息
        stats = vector_store.get_document_stats(kb_id)
        
        return {
            "success": True,
            "kb_id": kb_id,
            "documents": documents,
            "stats": stats,
            "count": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@app.get("/api/v1/stats/{kb_id}")
async def get_kb_stats(kb_id: str, sub: str = Depends(get_current_subject)):
    """获取知识库统计信息"""
    try:
        from app.services.vector_store import vector_store
        
        stats = vector_store.get_document_stats(kb_id)
        
        return {
            "success": True,
            "kb_id": kb_id,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@app.delete("/api/v1/knowledge-base/{kb_id}")
async def clear_knowledge_base(kb_id: str, sub: str = Depends(get_current_subject)):
    """清空指定知识库"""
    try:
        from app.services.vector_store import vector_store
        
        success = vector_store.clear_knowledge_base(kb_id)
        
        if success:
            return {
                "success": True,
                "message": f"知识库 '{kb_id}' 已清空",
                "kb_id": kb_id
            }
        else:
            raise HTTPException(status_code=500, detail="清空知识库失败")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空知识库失败: {str(e)}")


@app.get('/metrics')
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
