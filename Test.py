import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv

st.set_page_config(page_title="AI Agent Pro",page_icon="🤖")

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.title("🤖 My First AI Agent")
st.markdown("---")
st.write("Welcome, Karthick. Your AI Agent is online and ready for enterprise tasks.")


user_query = st.text_input("What is your command?",placeholder="e.g., Explain why AI is better then manual data entry..")

if st.button("Execute Command"):
    if user_query:
        with st.spinner("Agent is thinking..."):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages = [
                        {"role":"user","content":user_query}
                    ]
                )

                st.subheader("Agent Response:")
                st.success(response.choices[0].message.content)
            except Exception as e:
                st.error(f"Error:{e}")
    else:
        st.warning("Please enter a command first!")


