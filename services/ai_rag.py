"""
AI RAG Service - Quản lý Embeddings và Vector Database
"""
import os
from config import settings
from logger import get_logger

logger = get_logger("ai_rag")

# ── Embeddings (lazy load + cache) ────────────────────────────────────────────
_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        if settings.gemini_api_key:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            logger.info("Loading Google Gemini Embeddings...")
            _embeddings = GoogleGenerativeAIEmbeddings(
                model=settings.embedding_model, 
                google_api_key=settings.gemini_api_key
            )
        else:
            raise Exception("Missing Gemini API Key for Embeddings.")
    return _embeddings

# ── Vector Store (Supabase pgvector hoặc Pinecone) ────────────────────────────
_vector_store_instance = None

def get_vector_store():
    global _vector_store_instance
    if _vector_store_instance is None:
        embeddings = get_embeddings()
        
        # 1. Pinecone
        if settings.pinecone_api_key:
            try:
                from langchain_pinecone import PineconeVectorStore
                logger.info("Initializing Pinecone Vector Store...")
                _vector_store_instance = PineconeVectorStore(
                    index_name=settings.pinecone_index_name,
                    embedding=embeddings,
                    pinecone_api_key=settings.pinecone_api_key
                )
                return _vector_store_instance
            except ImportError:
                logger.error("Missing pinecone packages.")

        # 2. Supabase pgvector
        if settings.supabase_url and settings.supabase_key:
            try:
                from supabase.client import create_client
                from langchain_community.vectorstores import SupabaseVectorStore
                logger.info("Initializing Supabase Vector Store...")
                supabase_client = create_client(settings.supabase_url, settings.supabase_key)
                _vector_store_instance = SupabaseVectorStore(
                    embedding=embeddings,
                    client=supabase_client,
                    table_name="documents",
                    query_name="match_documents"
                )
                return _vector_store_instance
            except ImportError:
                logger.error("Missing supabase package.")
                
        # 3. Fallback (không dùng Chroma trên serverless)
        raise Exception("Không tìm thấy cấu hình Vector Database (Pinecone/Supabase)!")
            
    return _vector_store_instance


def format_docs(docs):
    return "\n\n---\n\n".join(
        f"[Nguồn: {os.path.basename(d.metadata.get('source', d.metadata.get('file_path', 'GTCC Data')))}]\n{d.page_content}"
        for d in docs
    )
