from typing import List, Optional, Tuple
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from app.config import settings
from loguru import logger

_DISTANCE = {"Cosine": rest.Distance.COSINE, "Euclid": rest.Distance.EUCLID, "Dot": rest.Distance.DOT}


class VectorStore:
    def __init__(self) -> None:
        self.client = None
        self.collection = settings.qdrant_collection
        self._initialized = False
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        if self._initialized:
            return
            
        try:
            self.client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
            
            # Check if collection exists, create if not
            try:
                self.client.get_collection(self.collection)
                logger.info(f"Collection '{self.collection}' already exists")
            except Exception:
                # Collection doesn't exist, create it
                self.client.create_collection(
                    collection_name=self.collection,
                    vectors_config=rest.VectorParams(
                        size=settings.embedding_dim,
                        distance=_DISTANCE.get(settings.qdrant_distance, rest.Distance.COSINE)
                    )
                )
                logger.info(f"Collection '{self.collection}' created successfully")
            
            self._initialized = True
            logger.info("VectorStore initialized successfully")
            
        except Exception as e:
            logger.error(f"Could not connect to Qdrant: {e}")
            self._initialized = False

    def upsert(self, points: List[Tuple[str, List[float], dict]]) -> None:
        if not self._initialized:
            self._ensure_collection()
        if not self._initialized:
            logger.error("Qdrant not available")
            return
            
        try:
            self.client.upsert(
                collection_name=self.collection,
                points=[
                    rest.PointStruct(id=pid, vector=vec, payload=payload) for pid, vec, payload in points
                ],
            )
            logger.info(f"Upserted {len(points)} points successfully")
        except Exception as e:
            logger.error(f"Failed to upsert: {e}")

    def search(self, query_vector: List[float], top_k: int = 5, filters: Optional[rest.Filter] = None):
        if not self._initialized:
            self._ensure_collection()
        if not self._initialized:
            logger.error("Qdrant not available")
            return []
            
        try:
            results = self.client.search(
                collection_name=self.collection,
                query_vector=query_vector,
                limit=top_k,
                query_filter=filters,
            )
            logger.info(f"Search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Failed to search: {e}")
            return []

    def get_documents(self, kb_id: str, limit: int = 100) -> List[dict]:
        """获取指定知识库的文档列表"""
        if not self._initialized:
            self._ensure_collection()
        if not self._initialized:
            logger.error("Qdrant not available")
            return []
            
        try:
            # 使用 scroll 方法获取所有点，然后按文档分组
            all_points = []
            offset = None
            
            while True:
                response = self.client.scroll(
                    collection_name=self.collection,
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False  # 不需要向量，节省带宽
                )
                
                points = response[0]  # scroll 返回 (points, next_page_offset)
                if not points:
                    break
                    
                all_points.extend(points)
                offset = response[1]  # next_page_offset
                
                if len(all_points) >= limit:
                    break
            
            # 按文档分组，去重
            documents = {}
            for point in all_points:
                payload = point.payload
                if payload and payload.get("kb_id") == kb_id:
                    doc_id = payload.get("doc_id", "unknown")
                    
                    if doc_id not in documents:
                        documents[doc_id] = {
                            "doc_id": doc_id,
                            "title": payload.get("title", "Unknown Title"),
                            "file_path": payload.get("file_path", ""),
                            "chunks_count": 0,
                            "first_page": float('inf'),
                            "last_page": 0,
                            "upload_time": payload.get("upload_time", ""),
                            "kb_id": kb_id
                        }
                    
                    # 统计块数和页码范围
                    documents[doc_id]["chunks_count"] += 1
                    page = payload.get("page", 1)
                    documents[doc_id]["first_page"] = min(documents[doc_id]["first_page"], page)
                    documents[doc_id]["last_page"] = max(documents[doc_id]["last_page"], page)
            
            # 转换为列表并按标题排序
            doc_list = list(documents.values())
            doc_list.sort(key=lambda x: x["title"])
            
            logger.info(f"Found {len(doc_list)} documents in knowledge base '{kb_id}'")
            return doc_list
            
        except Exception as e:
            logger.error(f"Failed to get documents: {e}")
            return []

    def get_document_stats(self, kb_id: str) -> dict:
        """获取知识库统计信息"""
        if not self._initialized:
            self._ensure_collection()
        if not self._initialized:
            return {"total_documents": 0, "total_chunks": 0, "kb_id": kb_id}
            
        try:
            documents = self.get_documents(kb_id)
            total_chunks = sum(doc["chunks_count"] for doc in documents)
            
            return {
                "total_documents": len(documents),
                "total_chunks": total_chunks,
                "kb_id": kb_id
            }
        except Exception as e:
            logger.error(f"Failed to get document stats: {e}")
            return {"total_documents": 0, "total_chunks": 0, "kb_id": kb_id}

    def clear_knowledge_base(self, kb_id: str) -> bool:
        """清空指定知识库的所有文档"""
        if not self._initialized:
            self._ensure_collection()
        if not self._initialized:
            logger.error("Qdrant not available")
            return False
            
        try:
            # 获取所有属于该知识库的点
            all_points = []
            offset = None
            
            while True:
                response = self.client.scroll(
                    collection_name=self.collection,
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )
                
                points = response[0]
                if not points:
                    break
                    
                # 过滤出属于指定知识库的点
                kb_points = [p for p in points if p.payload and p.payload.get("kb_id") == kb_id]
                all_points.extend(kb_points)
                offset = response[1]
                
                if not offset:
                    break
            
            if all_points:
                # 删除这些点
                point_ids = [p.id for p in all_points]
                self.client.delete(
                    collection_name=self.collection,
                    points_selector=rest.PointIdsList(
                        points=point_ids
                    )
                )
                logger.info(f"Cleared knowledge base '{kb_id}', deleted {len(point_ids)} points")
            else:
                logger.info(f"Knowledge base '{kb_id}' is already empty")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear knowledge base: {e}")
            return False


vector_store = VectorStore()
