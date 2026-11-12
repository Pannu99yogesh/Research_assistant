
import os
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

print("Testing Gemini connection...")

llm = ChatGoogleGenerativeAI(
    model=os.getenv("MODEL_NAME"),
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    timeout=120,
    max_retries=0,
    temperature=1,
    max_output_tokens=100,
)

start = time.time()

try:
    response = llm.invoke("Reply with exactly: Gemini is working!")
    print("\nResponse:", response.content)
    print("Time taken:", round(time.time() - start, 2), "seconds")

except Exception as e:
    print("\nError:", repr(e))
    print("Time taken:", round(time.time() - start, 2), "seconds")

