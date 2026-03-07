import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv
from pypdf import PdfReader


# 1. Helper Function to extract text from PDF
def get_pdf_text(pdf_file):
    text = ""
    pdf_reader = PdfReader(pdf_file)
    for page in pdf_reader.pages:
        content = page.extract_text()
        if content:  # Only add if text exists on the page
            text += content
    return text


# 2. Browser Tab & UI Setup
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
                document_text = get_pdf_text(uploaded_file)
            else:
                document_text = uploaded_file.getvalue().decode("utf-8")

            # Step B: Prepare the Enterprise Prompt
            full_prompt = f"Here is a document:\n\n{document_text}\n\nInstruction: {user_instruction}"

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
