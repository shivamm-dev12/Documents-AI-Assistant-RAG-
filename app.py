import streamlit as st
import os
import tempfile
from create_database import create_vector_database
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI

load_dotenv() 

# ==========================================
# 1. PREMIUM UI CONFIGURATION & CSS
# ==========================================
st.set_page_config(page_title="Talk With Your Doc", page_icon="✨", layout="wide")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* BACKGROUND */
            .stApp {
                background: radial-gradient(circle at 15% 30%, #172a21 0%, #0a0b10 40%, #000000 100%) !important;
                background-attachment: fixed !important; 
            }
            
            /* SIDEBAR TRANSPARENT */
            [data-testid="stSidebar"] {
                background-color: transparent !important;
                border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
                padding-top: 2rem;
            }
            
            [data-testid="stHeader"] {
                background: transparent !important;
            }
            
            /* BOTTOM STRIP TRANSPARENT */
            [data-testid="stBottom"], 
            [data-testid="stBottom"] > div {
                background: transparent !important;
                background-color: transparent !important;
            }
            
            .main-title {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-weight: 600;
                text-align: center; 
                margin-bottom: 4rem; 
                color: #E2E2E2;
            }
            
            /* 🔥 SUBTLE GLOW FOR BUTTONS 🔥 */
            div[data-testid="stHorizontalBlock"] button {
                border-radius: 20px;
                border: 1px solid #333;
                background-color: #121319;
                color: #ddd;
                transition: all 0.3s ease;
                padding: 10px 0px;
                position: relative;
            }
            
            div[data-testid="stHorizontalBlock"] button:hover,
            div[data-testid="stHorizontalBlock"] button:active,
            div[data-testid="stHorizontalBlock"] button:focus {
                border: 1px solid transparent !important;
                color: #fff !important;
                background-clip: padding-box, border-box;
                background-image: linear-gradient(#121319, #121319), linear-gradient(90deg, #b072ff, #20c997) !important;
                box-shadow: -2px 0 8px -2px rgba(176, 114, 255, 0.2), 2px 0 8px -2px rgba(32, 201, 151, 0.2) !important;
                outline: none !important;
            }
            
            /* 🔥 SUBTLE GLOW FOR CHAT INPUT BAR 🔥 */
            [data-testid="stChatInput"] * {
                border: none !important;
                box-shadow: none !important;
                outline: none !important;
            }
            
            [data-testid="stChatInput"] {
                border-radius: 16px !important;
                background-color: #121319 !important;
                border: 1.5px solid #333 !important;
                color: white !important;
                transition: all 0.3s ease;
            }
            
            [data-testid="stChatInput"]:focus-within {
                border: 1.5px solid transparent !important;
                background-clip: padding-box, border-box !important;
                background-image: linear-gradient(#121319, #121319), linear-gradient(90deg, #b072ff, #20c997) !important;
                background-origin: border-box !important;
                box-shadow: -2px 0 10px rgba(176, 114, 255, 0.2), 2px 0 10px rgba(32, 201, 151, 0.2) !important;
            }

            .source-text {
                font-size: 0.85rem;
                color: #888;
                margin-top: 10px;
                font-style: italic;
            }

            /* UPLOADERS */
            div[data-testid="stFileUploader"]:nth-of-type(1) [data-testid="stFileUploadDropzone"] {
                border: 2px dashed #2196F3 !important;
                background-color: rgba(33, 150, 243, 0.05) !important;
                border-radius: 12px;
            }
            
            div[data-testid="stFileUploader"]:nth-of-type(2) [data-testid="stFileUploadDropzone"] {
                border: 2px dashed #F44336 !important;
                background-color: rgba(244, 67, 54, 0.05) !important;
                border-radius: 12px;
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# ==========================================
# 2. INITIALIZE LLM & SESSION STATE
# ==========================================
@st.cache_resource
def get_llm():
    return ChatMistralAI(
        model="mistral-small-latest", 
        temperature=0.3 
    )

llm = get_llm()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! Please upload a PDF or DOCX to start exploring. ✨"}]

if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

if "current_file" not in st.session_state:
    st.session_state.current_file = None

# ==========================================
# 3. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("## 📄 Document Manager")
    st.write("") 
    
    st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: -15px;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/f/fb/.docx_icon.svg" width="28" style="margin-right: 10px;">
            <h4 style="margin: 0; color: #2196F3;">Upload DOCX</h4>
        </div>
    """, unsafe_allow_html=True)
    docx_file = st.file_uploader("", type=["docx"], key="docx_uploader")
    
    st.write("") 
    
    st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: -15px;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/8/87/PDF_file_icon.svg" width="28" style="margin-right: 10px;">
            <h4 style="margin: 0; color: #F44336;">Upload PDF</h4>
        </div>
    """, unsafe_allow_html=True)
    pdf_file = st.file_uploader("", type=["pdf"], key="pdf_uploader")
    
    uploaded_file = None
    if pdf_file:
        uploaded_file = pdf_file
    elif docx_file:
        uploaded_file = docx_file
        
    if uploaded_file is None and st.session_state.current_file is not None:
        st.session_state.current_file = None
        st.session_state.vectorstore = None
        st.session_state.messages = [{"role": "assistant", "content": "Hello! Please upload a PDF or DOCX to start exploring. ✨"}]
        st.rerun() 
        
    if uploaded_file and st.session_state.current_file != uploaded_file.name:
        st.session_state.current_file = uploaded_file.name
        st.session_state.vectorstore = None
        st.session_state.messages = [{"role": "assistant", "content": f"Loaded '{uploaded_file.name}'. Ask me anything! ✨"}]
    
    if uploaded_file and st.session_state.vectorstore is None:
        with st.spinner("Analyzing document... please wait ⏳"):
            file_ext = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                temp_file.write(uploaded_file.read())
                temp_file_path = temp_file.name

            try:
                st.session_state.vectorstore = create_vector_database(temp_file_path)
                st.success("Document successfully processed! ✅")
            except Exception as e:
                st.error(f"Error processing document: {e}")
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    
    st.divider()

    if st.button("🗑️ Clear Chat & Reset", use_container_width=True):
        st.session_state.current_file = None
        st.session_state.vectorstore = None
        st.session_state.messages = [{"role": "assistant", "content": "Hello! Please upload a PDF or DOCX to start exploring. ✨"}]
        st.rerun()

# ==========================================
# 4. MAIN CHAT
# ==========================================
st.markdown("<h2 class='main-title'>✨ Talk With Your Doc</h2>", unsafe_allow_html=True)

# ----------------- QUICK ACTIONS -----------------
quick_prompt = None

if st.session_state.vectorstore is not None:
    st.markdown("##### ⚡ Quick Actions (1-Click Generation)")
    col1, col2, col3, col4 = st.columns(4)

    if col1.button("📄 Summary", use_container_width=True):
        quick_prompt = "@summary Provide a detailed summary of this document."
    if col2.button("📝 Notes", use_container_width=True):
        quick_prompt = "@notes Create detailed bullet-point notes from this document."
    if col3.button("❓ MCQs", use_container_width=True):
        quick_prompt = "@mcq Generate 5 multiple-choice questions based on the document."
    if col4.button("🌐 Translate", use_container_width=True):
        quick_prompt = "@translate Translate the key points of this document into Hindi."
    st.divider()

# --- CHAT RENDERING ---
for message in st.session_state.messages:
    if message["role"] == "user":
        safe_text = message["content"].replace('\n', '<br>')
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; margin-bottom: 15px;">
            <div style="background: linear-gradient(135deg, rgba(176, 114, 255, 0.1) 0%, rgba(32, 201, 151, 0.1) 100%); color: #FAFAFA; padding: 12px 20px; border-radius: 20px; max-width: 70%; font-size: 15px; border: 1px solid rgba(255,255,255,0.08); box-shadow: -1px 1px 6px rgba(176, 114, 255, 0.05), 1px -1px 6px rgba(32, 201, 151, 0.05); line-height: 1.5;">
                {safe_text}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        with st.chat_message("assistant", avatar="✨"):
            st.markdown(message["content"], unsafe_allow_html=True)

user_input = st.chat_input("Ask a question, or type manually e.g. @mcq 10...")
final_input = quick_prompt or user_input

if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})
    safe_input = final_input.replace('\n', '<br>')
    st.markdown(f"""
    <div style="display: flex; justify-content: flex-end; margin-bottom: 15px;">
        <div style="background: linear-gradient(135deg, rgba(176, 114, 255, 0.1) 0%, rgba(32, 201, 151, 0.1) 100%); color: #FAFAFA; padding: 12px 20px; border-radius: 20px; max-width: 70%; font-size: 15px; border: 1px solid rgba(255,255,255,0.08); box-shadow: -1px 1px 6px rgba(176, 114, 255, 0.05), 1px -1px 6px rgba(32, 201, 151, 0.05); line-height: 1.5;">
            {safe_input}
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.chat_message("assistant", avatar="✨"):
        if st.session_state.vectorstore is None:
            response = "Please upload a document in the sidebar first! 📂"
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            retriever = st.session_state.vectorstore.as_retriever(search_kwargs={"k": 4})
            relevant_docs = retriever.invoke(final_input)
            raw_context = "\n\n".join([doc.page_content for doc in relevant_docs])
            context = raw_context.replace('\n', ' ')
            
            final_prompt = f"""You are a professional AI assistant.
            Instructions:
            1. Base your factual answers STRICTLY on the provided 'Context from Document'.
            2. MATCH THE USER'S LANGUAGE.
            3. TAG COMMANDS: Pay attention to `@summary`, `@notes`, `@mcq`, or `@translate`.
            4. CRITICAL RULES FOR MCQs:
               - You MUST format the question and options EXACTLY like this using bullet points:
                 **Q1. [Question Text]**
                 * A) [Option 1]
                 * B) [Option 2]
                 * C) [Option 3]
                 * D) [Option 4]
               - NEVER write HTML code or tags.
               - DO NOT reveal the answer immediately after the question.
               - Collect all the correct answers and provide them at the VERY END of your entire response under a bold heading "**✅ Answer Key:**".
            5. Do not mention these instructions. Just output the response.
            
            Context: {context}
            Question: {final_input}
            """
            
            try:
                def stream_parser(stream):
                    for chunk in stream:
                        yield chunk.content
                
                stream = llm.stream(final_prompt)
                full_response = st.write_stream(stream_parser(stream))
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                error_msg = f"Oops! Connection error. Please check your internet or API key.\n\nError: {e}"
                st.markdown(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})