import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
print("-----CONNECTING TO AI-----")
try:
   response = groq_client.chat.completions.create(
        messages=[
            {"role": "user", "content": "Hello! Give me one short tip for an AI student."}
        ],
        model="llama-3.3-70b-versatile",
    )
   print("--- GROQ AI IS ONLINE ---")
   print(response.choices[0].message.content)
except Exception as e:
    print(f"---ERROR OCCURRED----")
    print(e)


































# import os
# from google import genai
# from dotenv import load_dotenv

# load_dotenv()
# client = genai.Client(api_key=os.getenv("API_KEY"))

# print("-----CONNECTING TO AI-----")

# try:
#     response = client.models.generate_content(
#         model='gemini-2.0-flash',
#         contents="Hello! Give me one tip for a new AI student."
#     )
#     print("----AI IS ONLINE------")
#     print(response.text)
# except Exception as e:
#     print(f"---ERROR OCCURRED----")
#     print(e)


