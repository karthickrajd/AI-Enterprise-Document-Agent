import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from chromadb.utils import embedding_functions

# --- 1. SETUP & SYSTEM INITIALIZATION ---
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Persistent Vector Database (The "Closet")
chroma_client = chromadb.PersistentClient(path="./my_vector_db")
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
collection = chroma_client.get_or_create_collection(
    name="library", embedding_function=sentence_transformer_ef
)

# --- 2. SESSION STATE (The "App Memory") ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = []
if "processing" not in st.session_state:
    st.session_state.processing = False


# --- 3. HELPER FUNCTIONS ---
def get_pdf_text(pdf_file):
    text = ""
    pdf_reader = PdfReader(pdf_file)
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text


def get_text_chunks(raw_text):
    return RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200
    ).split_text(raw_text)


# --- 4. UI LAYOUT ---
st.set_page_config(page_title="Enterprise Knowledge Hub", layout="wide")
st.title("🏛️ Enterprise Knowledge Hub")

with st.sidebar:
    # EMERGENCY UNLOCK: Only shows up if the app is stuck
    if st.session_state.processing:
        if st.button("🔓 Emergency Unlock UI"):
            st.session_state.processing = False
            st.rerun()

    st.header("👤 AI Expert Persona")
    persona = st.selectbox(
        "Choose AI Role:",
        ["General Assistant", "Legal Expert", "Financial Advisor", "IT Engineer"],
        disabled=st.session_state.processing,
    )

    st.divider()
    st.header("📁 Document Library")
    uploaded_files = st.file_uploader(
        "Upload PDFs",
        type="pdf",
        accept_multiple_files=True,
        disabled=st.session_state.processing,
    )

    # --- INDEXING LOGIC ---
    if st.button("📚 Index All Files", disabled=st.session_state.processing):
        if not uploaded_files:
            st.warning("Please upload files first.")
        else:
            st.session_state.processing = True
            try:
                for file in uploaded_files:
                    if file.name not in st.session_state.indexed_files:
                        with st.spinner(f"Indexing {file.name}..."):
                            text = get_pdf_text(file)
                            chunks = get_text_chunks(text)
                            collection.add(
                                documents=chunks,
                                ids=[f"{file.name}_{i}" for i in range(len(chunks))],
                                metadatas=[
                                    {"source": file.name} for _ in range(len(chunks))
                                ],
                            )
                            st.session_state.indexed_files.append(file.name)
                st.success("Library Updated!")
            except Exception as e:
                st.error(f"Indexing Error: {e}")
            finally:
                st.session_state.processing = False
                st.rerun()

    # --- THE MISSING PART: CURRENT LIBRARY DISPLAY ---
    if st.session_state.indexed_files:
        st.write("---")
        st.write("✅ **In Library:**")
        for f in st.session_state.indexed_files:
            st.write(f"📄 {f}")
        st.write("---")

    # --- COMPARISON LOGIC ---
    if st.button("⚖️ Compare Documents", disabled=st.session_state.processing):
        if len(st.session_state.indexed_files) < 2:
            st.warning("⚠️ Index at least 2 files to compare.")
        else:
            st.session_state.processing = True
            with st.spinner("🔍 Comparing..."):
                try:
                    all_context = ""
                    for filename in st.session_state.indexed_files:
                        # Safety: Grab 5 chunks per file to stay under 12k tokens
                        file_data = collection.get(where={"source": filename}, limit=5)
                        content = "\n".join(file_data["documents"])
                        all_context += f"\n--- FILE: {filename} ---\n{content[:3000]}\n"

                    res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "user",
                                "content": f"Compare these files in a Markdown table:\n{all_context}",
                            }
                        ],
                    )
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": f"### ⚖️ Comparison Results\n{res.choices[0].message.content}",
                        }
                    )
                except Exception as e:
                    st.error(f"Comparison Error: {e}")
                finally:
                    st.session_state.processing = False
                    st.rerun()

    if st.button("🗑️ Reset Library", disabled=st.session_state.processing):
        try:
            chroma_client.delete_collection("library")
            st.session_state.indexed_files = []
            st.session_state.messages = []
            st.success("Library Cleared!")
            st.rerun()
        except:
            st.rerun()

# --- 5. CHAT INTERFACE ---
# Display messages from memory
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input(
    "Ask about your library...", disabled=st.session_state.processing
):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Searching Library..."):
        try:
            # RAG Search: Find the most relevant snippets
            results = collection.query(query_texts=[prompt], n_results=5)
            context = "\n\n".join(
                [
                    f"[{m['source']}]: {d}"
                    for d, m in zip(results["documents"][0], results["metadatas"][0])
                ]
            )

            # AI Logic with Persona
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "user",
                        "content": f"You are a {persona}. Context:\n{context}\n\nQuestion: {prompt}",
                    }
                ],
            )
            ai_ans = res.choices[0].message.content
            with st.chat_message("assistant"):
                st.markdown(ai_ans)
            st.session_state.messages.append({"role": "assistant", "content": ai_ans})
        except Exception as e:
            st.error(f"Chat Error: {e}")
