import os
import uuid
from typing import List, Dict, Tuple
from pypdf import PdfReader
from loguru import logger
from app.services.embeddings import embeddings
from app.services.vector_store import vector_store


class PDFProcessor:
    def __init__(self):
        self.chunk_size = 1000  # 字符数
        self.chunk_overlap = 200  # 重叠字符数

    async def process_pdf(self, file_path: str, kb_id: str, title: str = None) -> Dict:
        """处理 PDF 文件并存储到向量数据库"""
        try:
            # 读取 PDF
            text_content = self._extract_text(file_path)
            if not text_content:
                raise ValueError("无法从 PDF 提取文本内容")

            # 分块处理
            chunks = self._chunk_text(text_content)
            logger.info(f"PDF 分块完成，共 {len(chunks)} 个块")

            # 生成嵌入向量
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings_list = await embeddings.create_embeddings(chunk_texts)
            
            if not embeddings_list:
                raise ValueError("生成嵌入向量失败")

            # 准备存储数据
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings_list)):
                point_id = str(uuid.uuid4())
                payload = {
                    "doc_id": os.path.basename(file_path),
                    "title": title or os.path.basename(file_path),
                    "content": chunk["text"],
                    "page": chunk["page"],
                    "chunk_id": i,
                    "kb_id": kb_id,
                    "file_path": file_path
                }
                
                points.append((point_id, embedding, payload))

            # 存储到向量数据库
            vector_store.upsert(points)
            logger.info(f"成功存储 {len(points)} 个向量到数据库")

            return {
                "success": True,
                "message": f"PDF 处理完成，共处理 {len(chunks)} 个文本块",
                "chunks_count": len(chunks),
                "file_path": file_path,
                "title": title or os.path.basename(file_path)
            }

        except Exception as e:
            logger.error(f"PDF 处理失败: {e}")
            return {
                "success": False,
                "message": f"PDF 处理失败: {str(e)}",
                "error": str(e)
            }

    def _extract_text(self, file_path: str) -> str:
        """从 PDF 提取文本"""
        try:
            reader = PdfReader(file_path)
            text = ""
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"PDF 文本提取失败: {e}")
            raise

    def _chunk_text(self, text: str) -> List[Dict]:
        """将文本分块"""
        chunks = []
        start = 0
        
        while start < len(text):
            # 计算块结束位置
            end = start + self.chunk_size
            
            # 如果不是最后一块，尝试在句子边界分割
            if end < len(text):
                # 寻找最近的句号、问号或感叹号
                for i in range(end, max(start, end - 100), -1):
                    if text[i] in '.!?。！？':
                        end = i + 1
                        break
            
            # 提取当前块
            chunk_text = text[start:end].strip()
            if chunk_text:
                # 估算页码（简单估算）
                page_estimate = (start // 2000) + 1
                
                chunks.append({
                    "text": chunk_text,
                    "page": page_estimate,
                    "start": start,
                    "end": end
                })
            
            # 移动到下一块，考虑重叠
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks


pdf_processor = PDFProcessor()
