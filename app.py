import streamlit as st
import os
import tempfile
from create_database import create_vector_database
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
import streamlit.components.v1 as components

load_dotenv() 

# ==========================================
# 1. PREMIUM UI CONFIGURATION & CSS
# ==========================================
st.set_page_config(page_title="Talk With Your Doc", page_icon="✨", layout="wide")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            
            /* Hide Streamlit deployment badge/decoration but KEEP the top header bar */
            [data-testid="stDecoration"] {display: none;}
            header {
                background: transparent !important;
                visibility: visible !important;
            }
            
            /* BACKGROUND */
            .stApp {
                background: radial-gradient(circle at 15% 30%, #172a21 0%, #0a0b10 40%, #000000 100%) !important;
                background-attachment: fixed !important; 
            }
            
            /* SIDEBAR RESPONSIVE & TRANSPARENT */
            [data-testid="stSidebar"] {
                background-color: rgba(12, 13, 18, 0.95) !important;
                border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
                padding-top: 1rem;
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
                margin-bottom: 2rem; 
                color: #E2E2E2;
            }
            
            /* SUBTLE GLOW FOR CHAT INPUT BAR */
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
            
            /* 🔥 MAGIC CSS FOR CENTERING UPLOADER 🔥 */
            [data-testid="stFileUploader"] {
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
            }
            [data-testid="stFileUploader"] section {
                background: transparent !important;
                border: none !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                width: 100% !important;
            }
            [data-testid="stFileUploader"] div, 
            [data-testid="stFileUploader"] small {
                text-align: center !important;
                align-items: center !important;
                justify-content: center !important;
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

# --- CLEAN WELCOME MESSAGE ---
welcome_msg = "Hello! Ask me anything, or upload a PDF/DOCX to explore your documents. ✨"

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": welcome_msg}]

if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

if "current_file" not in st.session_state:
    st.session_state.current_file = None

# ==========================================
# 3. SIDEBAR (MOBILE FRIENDLY DOCUMENT MANAGER)
# ==========================================
with st.sidebar:
    st.markdown("## 📄 Document Manager")
    st.markdown("<p style='color: #888; font-size: 0.9rem; margin-top: -5px; margin-bottom: 25px; text-align: center;'>📁 Select your file type below</p>", unsafe_allow_html=True)
    
    # --- DOCX SECTION (CENTERED) ---
    st.markdown("<h4 style='text-align: center; color: #2196F3; font-size: 16px; margin-bottom: -15px;'>📄 Upload DOCX</h4>", unsafe_allow_html=True)
    docx_file = st.file_uploader("docx_up", type=["docx"], key="docx_uploader", label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True) 
    
    # --- PDF SECTION (CENTERED) ---
    st.markdown("<h4 style='text-align: center; color: #F44336; font-size: 16px; margin-bottom: -15px;'>📕 Upload PDF</h4>", unsafe_allow_html=True)
    pdf_file = st.file_uploader("pdf_up", type=["pdf"], key="pdf_uploader", label_visibility="collapsed")
    
    uploaded_file = None
    if pdf_file:
        uploaded_file = pdf_file
    elif docx_file:
        uploaded_file = docx_file
        
    if uploaded_file is None and st.session_state.current_file is not None:
        st.session_state.current_file = None
        st.session_state.vectorstore = None
        st.session_state.messages = [{"role": "assistant", "content": welcome_msg}]
        st.rerun() 
        
    if uploaded_file and st.session_state.current_file != uploaded_file.name:
        st.session_state.current_file = uploaded_file.name
        st.session_state.vectorstore = None
        st.session_state.messages = [{"role": "assistant", "content": f"Loaded '{uploaded_file.name}'. Ask me anything about it! ✨"}]
    
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
        st.session_state.messages = [{"role": "assistant", "content": welcome_msg}]
        st.rerun()

# ==========================================
# 4. CONDITIONAL TITLE & DYNAMIC MOBILE HINT
# ==========================================
title_placeholder = st.empty()

# Ye block sirf tab run hoga jab chat khali ho
if len(st.session_state.messages) <= 1 and st.session_state.current_file is None:
    # Title aur Mobile Tooltip dono ek sath inject karenge
    title_placeholder.markdown("""
        <h1 class='main-title'>✨ Talk With Your Doc</h1>
        <style>
        @media (max-width: 768px) {
            header::after {
                content: "👈 Upload doc";
                position: fixed;
                top: 14px;
                left: 55px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 11px;
                font-weight: 500;
                background-color: rgba(255, 255, 255, 0.08);
                padding: 4px 10px;
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                z-index: 999999;
                pointer-events: none;
            }
        }
        </style>
    """, unsafe_allow_html=True)

# ----------------- QUICK ACTIONS -----------------
quick_prompt = None

if st.session_state.vectorstore is not None:
    st.markdown("##### ⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("📄 Summary", use_container_width=True):
        quick_prompt = "@summary Provide a detailed summary."
    if col2.button("📝 Notes", use_container_width=True):
        quick_prompt = "@notes Create detailed bullet-point notes."
    if col3.button("❓ MCQs", use_container_width=True):
        quick_prompt = "@mcq Generate 5 MCQs."
    if col4.button("🌐 Translate", use_container_width=True):
        quick_prompt = "@translate Translate key points to Hindi."
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

# 🚀 AUTO-SCROLL SCRIPT FOR CHAT
components.html(
    """
    <script>
        var body = window.parent.document.querySelector('.main');
        if (body) {
            body.scrollTop = body.scrollHeight;
        }
    </script>
    """,
    height=0,
)

# 🚀 CHAT INPUT BAR
user_input = st.chat_input("Ask a question, or upload document from sidebar 📂")
final_input = quick_prompt or user_input

if final_input:
    # JAISE HI USER MESSAGE BHEJEGA, TITLE AUR TOOLTIP DONO GAYAB HO JAYENGE!
    title_placeholder.empty()
    
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
        try:
            def stream_parser(stream):
                for chunk in stream:
                    yield chunk.content

            if st.session_state.vectorstore is None:
                # NORMAL CHATBOT MODE
                general_prompt = f"You are a helpful AI assistant. Answer the following query clearly and concisely: {final_input}"
                stream = llm.stream(general_prompt)
                full_response = st.write_stream(stream_parser(stream))
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            else:
                # DOCUMENT CHATBOT MODE (RAG)
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
                
                stream = llm.stream(final_prompt)
                full_response = st.write_stream(stream_parser(stream))
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
        except Exception as e:
            error_msg = f"Oops! Connection error. Please check your internet or API key.\n\nError: {e}"
            st.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})