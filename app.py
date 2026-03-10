import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from chromadb.utils import embedding_functions

# --- 1. SETUP & INITIALIZATION ---
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="./my_vector_db")
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# --- 2. CHAT MEMORY SETUP ---
# This "Session State" keeps our chat history alive even when the page refreshes
if "messages" not in st.session_state:
    st.session_state.messages = []  # This is our "History Notebook"
if "current_file" not in st.session_state:
    st.session_state.current_file = None


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
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return text_splitter.split_text(raw_text)


# --- 4. UI LAYOUT ---
st.set_page_config(page_title="Enterprise AI Chat", layout="wide")
st.title("💼 Enterprise Knowledge Agent")

# Sidebar for File Uploads
with st.sidebar:
    st.header("📁 Document Center")
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

    # If the uploader is empty, reset the filename in memory
    if uploaded_file is None:
        st.session_state.current_file = None

    if st.button("Index Document"):
        if uploaded_file:
            with st.spinner("Processing..."):
                # Save the name only when we actually index it
                st.session_state.current_file = uploaded_file.name  # Save filename
                raw_text = get_pdf_text(uploaded_file)
                chunks = get_text_chunks(raw_text)

                # Reset & Fill Vector DB
                try:
                    chroma_client.delete_collection("docs")
                except:
                    pass

                collection = chroma_client.create_collection(
                    name="docs", embedding_function=sentence_transformer_ef
                )
                collection.add(
                    documents=chunks, ids=[f"id_{i}" for i in range(len(chunks))]
                )
                st.success(f"Indexed: {st.session_state.current_file}")

                # NEW: Auto-generate a summary for the Sidebar
                with st.spinner("Summarizing for dashboard..."):
                    # We grab the first 3 chunks to get the "Introduction"
                    summary_context = "\n\n".join(chunks[:3])
                    summary_response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "user",
                                "content": f"Provide a 3-bullet point summary of this document start:\n\n{summary_context}",
                            }
                        ],
                    )
                    st.session_state.doc_summary = summary_response.choices[
                        0
                    ].message.content

    st.divider()

    if "doc_summary" in st.session_state and st.session_state.current_file:
        st.sidebar.markdown("### 📝 Quick Summary")
        st.sidebar.info(st.session_state.doc_summary)

    # FEATURE 2: Clear Chat Button
    if st.button("🧹 Clear Chat History"):
        st.session_state.messages = []
        st.rerun()


# Display current file status
if st.session_state.current_file:
    st.info(f"Currently chatting with: **{st.session_state.current_file}**")


# --- 5. CHAT INTERFACE ---
# Display previous messages from our "Notebook"
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input Box (The Chat Bubble)
if prompt := st.chat_input("Ask me anything about your document..."):
    # A. Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # B. RAG Logic: Find relevant snippets
    with st.spinner("Searching document..."):
        collection = chroma_client.get_collection(
            name="docs", embedding_function=sentence_transformer_ef
        )
        results = collection.query(query_texts=[prompt], n_results=3)
        context = "\n\n".join(results["documents"][0])

        # FEATURE 1: Source Citations (Preparing the snippets)
        sources_text = "\n\n**Sources found in document:**\n" + "\n".join(
            [f"- {d[:100]}..." for d in results["documents"][0]]
        )

        # C. Send to AI with History
        full_prompt = f"Use this context to answer: {context}\n\nQuestion: {prompt}"

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": full_prompt}],
            )
            # Combine answer with sources
            ai_answer = response.choices[0].message.content + "\n" + sources_text

            # D. Display AI message & Save to history
            with st.chat_message("assistant"):
                st.markdown(ai_answer)
            st.session_state.messages.append(
                {"role": "assistant", "content": ai_answer}
            )
        except Exception as e:
            st.error(f"Error: {e}")
