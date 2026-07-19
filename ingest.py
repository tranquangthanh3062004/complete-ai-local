from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

# 1. Định nghĩa đường dẫn
pdf_path = "./data/luat_giao_thong.pdf"
persist_directory = "./chroma_db"

print("Đang đọc file PDF...")
# 2. Đọc file PDF
loader = PyPDFLoader(pdf_path)
documents = loader.load()

print("Đang chia nhỏ văn bản...")
# 3. Chia nhỏ văn bản (Mỗi đoạn 1000 ký tự, giữ lại 200 ký tự trùng lặp để không đứt ý)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = text_splitter.split_documents(documents)

from langchain_google_genai import GoogleGenerativeAIEmbeddings

print("Đang tải mô hình Embedding Gemini...")
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

print("Đang lưu vào ChromaDB...")
# 5. Lưu vào ChromaDB
vector_db = Chroma.from_documents(
    documents=chunks, 
    embedding=embeddings, 
    persist_directory=persist_directory
)

print("Hoàn tất! Dữ liệu đã được lưu trữ trong thư mục chroma_db.")

if __name__ == "__main__":
    pass
