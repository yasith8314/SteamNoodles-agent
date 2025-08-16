import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def ask_llm(prompt: str, temperature: float = 0.4) -> str:
    client = Groq(
        api_key = GROQ_API_KEY
    )
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192",
        temperature=temperature
    )
    return chat_completion.choices[0].message.content.strip()
