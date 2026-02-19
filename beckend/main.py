import os
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Product Expert API")

# ✅ CORS (Vercel frontend allow)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # production me specific domain dal sakte ho
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Message model (for chat history)
class Message(BaseModel):
    role: str
    content: str

# ✅ Request model (list of messages)
class ChatRequest(BaseModel):
    messages: List[Message]

# ✅ Health check
@app.get("/")
def home():
    return {"status": "API is running 🚀"}

# ✅ Chat endpoint
@app.post("/chat")
def chat(request: ChatRequest):
    try:
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            return {"error": "GROQ API key not found"}

        client = Groq(api_key=api_key)


        # System prompt + full chat history
        all_messages = [
            {
                "role": "system",
                "content": "You are an AI Product Expert. Help users choose the best products. Remember previous conversation context."
            }
        ] + [msg.dict() for msg in request.messages]

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=all_messages
        )

        reply = response.choices[0].message.content

        return {"reply": reply}

    except Exception as e:
        return {"error": str(e)}
