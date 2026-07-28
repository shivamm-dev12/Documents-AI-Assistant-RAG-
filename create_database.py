import os
import re
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

# Bijli jaisi speed ke liye Mistral Embeddings ⚡
from langchain_mistralai import MistralAIEmbeddings

load_dotenv()

def create_vector_database(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        loader = PyPDFLoader(file_path)
    elif ext == '.docx':
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload PDF or DOCX.")
        
    docs = loader.load()
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(docs)

    # ==========================================
    # 🛡️ THE ULTIMATE TITANIUM FILTER 🛡️
    # ==========================================
    clean_chunks = []
    for chunk in chunks:
        # Check karo ki chunk exist karta hai aur string hai
        if chunk.page_content and isinstance(chunk.page_content, str):
            # Null bytes (\x00) aur faltu spaces ko hatao
            text = chunk.page_content.replace('\x00', '').strip()
            
            # Regex check: Ensure karo ki kam se kam ek number ya alphabet ho!
            # Isse sirf symbols ya blank spaces wale chunks reject ho jayenge.
            if len(text) > 10 and re.search(r'[a-zA-Z0-9]', text):
                chunk.page_content = text
                clean_chunks.append(chunk)

    if not clean_chunks:
        raise ValueError("⚠️ Error: Is document mein koi readable text nahi mila. Ye shayad ek scanned PDF hai ya corrupt hai!")

    embedding_model = MistralAIEmbeddings(model="mistral-embed")

    vectorstore = Chroma.from_documents(
        documents=clean_chunks,
        embedding=embedding_model,
        persist_directory="chroma_db"
    )

    return vectorstore