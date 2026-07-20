from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
import os
from dotenv import load_dotenv

# HUGGINGFACE HATA KAR MISTRAL EMBEDDINGS LAGA DIYA HAI (Bijli jaisi speed ke liye ⚡)
from langchain_mistralai import MistralAIEmbeddings

load_dotenv()

def create_vector_database(file_path):
    # -------------------
    # Load document (PDF or DOCX)
    # -------------------
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        loader = PyPDFLoader(file_path)
    elif ext == '.docx':
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload PDF or DOCX.")
        
    docs = loader.load()
    
    # -------------------
    # Chunking (Size bada kar diya hai taaki fast processing ho)
    # -------------------
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(docs)

    # Filter out empty chunks
    clean_chunks = [chunk for chunk in chunks if chunk.page_content and str(chunk.page_content).strip()]

    # --------------------------
    # Initialize SUPERFAST API embedding model
    # --------------------------
    embedding_model = MistralAIEmbeddings(model="mistral-embed")

    # -----------------------
    # Creating vector store
    # -----------------------
    vectorstore = Chroma.from_documents(
        documents=clean_chunks,
        embedding=embedding_model,
        persist_directory="chroma_db"
    )

    return vectorstore