import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from chromadb.utils import embedding_functions

# --- SETUP ---
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="./my_vector_db")
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)


# --- FUNCTIONS ---
def get_pdf_text(pdf_file):
    text = ""
    pdf_reader = PdfReader(pdf_file)
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text


def get_text_chunks(raw_text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, length_function=len
    )
    return text_splitter.split_text(raw_text)


# --- UI ---
st.set_page_config(page_title="Enterprise AI Agent", page_icon="💼")
st.title("💼 Enterprise AI Document Agent")
st.write("Upload a document to search its meaning using RAG technology.")

uploaded_file = st.file_uploader("Upload a Business Document", type=["txt", "pdf"])
user_instruction = st.text_input(
    "Ask a question about this file:",
    value="What are the key points of this document?",
)

if st.button("Analyze Document"):
    if uploaded_file is not None:
        with st.spinner("🧠 Vectorizing and Searching..."):
            # 1. Extract Text
            if uploaded_file.type == "application/pdf":
                raw_text = get_pdf_text(uploaded_file)
            else:
                raw_text = uploaded_file.getvalue().decode("utf-8")

            # 2. Chunking
            text_chunks = get_text_chunks(raw_text)

            # 3. RESET COLLECTION (The Fix for the ValueError)
            try:
                chroma_client.delete_collection(name="corporate_docs")
            except:
                pass

            collection = chroma_client.create_collection(
                name="corporate_docs", embedding_function=sentence_transformer_ef
            )

            # 4. STORE
            ids = [f"id_{i}" for i in range(len(text_chunks))]
            collection.add(documents=text_chunks, ids=ids)

            # 5. VECTOR QUERY
            results = collection.query(
                query_texts=[user_instruction],
                n_results=5,
            )

            final_context = "\n\n".join(results["documents"][0])

            # 6. LLM CALL
            full_prompt = f"Use these snippets to answer: {user_instruction}\n\nSnippets:\n{final_context}"

            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": full_prompt}],
                )

                st.subheader("Analysis Result:")
                st.success(response.choices[0].message.content)
                st.download_button(
                    label="📥 Download Report",
                    data=response.choices[0].message.content,
                    file_name="Report.txt",
                )
            except Exception as e:
                st.error(f"AI Error: {e}")
    else:
        st.warning("Please upload a file first!")
