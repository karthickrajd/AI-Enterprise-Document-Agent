import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


# 1. Extract text from PDF (You already built this!)
def get_pdf_text(pdf_file):
    text = ""
    pdf_reader = PdfReader(pdf_file)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


# 2. Slice the text (New Tool!)
def get_text_chunks(raw_text):
    # For a professional project, 1000/200 is a standard starting point
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, length_function=len
    )
    chunks = text_splitter.split_text(raw_text)
    return chunks


# 3. Test it
st.set_page_config(page_title="Enterprise AI Agent", page_icon="💼")
load_dotenv()

# 3. Initialize AI Brain (Groq)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.title("💼 Enterprise AI Document Agent")
st.write("Upload a business document, and I will analyze it using Llama 3.3.")

# 4. User Inputs
uploaded_file = st.file_uploader("Upload a Business Document", type=["txt", "pdf"])
user_instruction = st.text_input(
    "What should I do with this file?",
    value="Summarize this document in 3 bullet points.",
)

# 5. The Core Logic (The "Action" Button)
if st.button("Analyze Document"):
    if uploaded_file is not None:
        with st.spinner("Processing document..."):
            # Step A: Extract text based on file type
            if uploaded_file.type == "application/pdf":
                raw_text = get_pdf_text(uploaded_file)
            else:
                raw_text = uploaded_file.getvalue().decode("utf-8")
                raw_text = get_pdf_text(uploaded_file)

            # 2. Slice it into small chunks (Crucial!)
            text_chunks = get_text_chunks(raw_text)
            st.write(f"✅ Document split into {len(text_chunks)} chunks.")

            # 3. THE FILTER (The Quick Fix)
            # We search for chunks that contain keywords from the user's instruction
            relevant_chunks = []
            keywords = user_instruction.lower().split()

            for chunk in text_chunks:
                for word in keywords:
                    if word in chunk.lower():
                        relevant_chunks.append(chunk)
                        break  # Found a match, move to next chunk

            # 4. Limit the size (Don't exceed 12,000 tokens)
            # We only take the first 5 relevant chunks
            final_context = "\n\n".join(relevant_chunks[:5])

            # If no keywords match, just take the first 5 chunks as a fallback
            if not final_context:
                final_context = "\n\n".join(text_chunks[:5])

            # 5. Send only the "Filtered" context to the AI
            full_prompt = f"Based ONLY on the following snippets, {user_instruction}\n\nSnippets:\n{final_context}"

            # Step C: Send to AI Brain
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": full_prompt}],
                )

                st.subheader("Analysis Result:")
                st.success(response.choices[0].message.content)
                report_text = response.choices[0].message.content
                st.download_button(
                    label="📥 Download Analysis Report",
                    data=report_text,
                    file_name="AI_Analysis_Report.txt",
                    mime="text/plain",
                )
            except Exception as e:
                st.error(f"AI Error: {e}")
    else:
        st.warning("Please upload a file first!")
