"""
AI RAG Service - Quản lý Embeddings và Vector Database
"""
import os
from config import settings
from logger import get_logger

logger = get_logger("ai_rag")

_embeddings_cache = {}

def get_embeddings(engine: str = None):
    engine_type = engine or getattr(settings, "embedding_engine", "gemini")
    if engine_type in _embeddings_cache:
        return _embeddings_cache[engine_type]

    if engine_type == "huggingface" or not settings.gemini_api_key:
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            logger.info("Loading Local HuggingFace Embeddings (all-MiniLM-L6-v2)...")
            emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            _embeddings_cache[engine_type] = emb
            return emb
        except Exception as e:
            logger.warning(f"HuggingFace embeddings error: {e}")
            
    if settings.gemini_api_key:
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            logger.info("Loading Google Gemini Embeddings...")
            emb = GoogleGenerativeAIEmbeddings(
                model=settings.embedding_model, 
                google_api_key=settings.gemini_api_key
            )
            _embeddings_cache[engine_type] = emb
            return emb
        except Exception as e:
            logger.warning(f"Gemini embeddings error: {e}")
            
    from langchain_community.embeddings import HuggingFaceEmbeddings
    emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    _embeddings_cache[engine_type] = emb
    return emb

# ── Vector Store (Supabase pgvector hoặc Pinecone) ────────────────────────────
_vector_store_instance = None

def get_vector_store():
    global _vector_store_instance
    if _vector_store_instance is None:
        embeddings = get_embeddings()
        
        # 1. Supabase pgvector (Ưu tiên số 1 cho Production)
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
                logger.error("Missing supabase package. Run: pip install supabase")

        # 2. Pinecone (Lựa chọn thay thế)
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
            except Exception as e:
                logger.warning(f"Pinecone vector store error or index not found: {e}. Falling back to local ChromaDB.")
                
        # 3. Local ChromaDB Fallback for Dev & Offline
        try:
            from langchain_community.vectorstores import Chroma
            logger.info("Initializing Local ChromaDB Vector Store...")
            chroma_dir = getattr(settings, 'chroma_persist_dir', './chroma_db')
            os.makedirs(chroma_dir, exist_ok=True)
            # Dùng HuggingFace embeddings cho local ChromaDB để 100% không phụ thuộc API key và 0% rate limit
            local_embeddings = get_embeddings(engine="huggingface")
            _vector_store_instance = Chroma(
                collection_name="gtcc_docs",
                embedding_function=local_embeddings,
                persist_directory=chroma_dir
            )
            return _vector_store_instance
        except Exception as e:
            logger.warning(f"ChromaDB local fallback failed: {e}. Falling back to InMemoryVectorStore.")
            from langchain_core.vectorstores import InMemoryVectorStore
            _vector_store_instance = InMemoryVectorStore(embedding=embeddings)
            return _vector_store_instance
            
    return _vector_store_instance


def format_docs(docs):
    return "\n\n---\n\n".join(
        f"[Nguồn: {os.path.basename(d.metadata.get('source', d.metadata.get('file_path', 'GTCC Data')))}]\n{d.page_content}"
        for d in docs
    )
