import os
from typing import List
from fastapi import FastAPI
from fastapi import Request
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

    class Config:
        extra = "allow"

# ✅ Request model (list of messages)
class ChatRequest(BaseModel):
    messages: List[Message]

# ✅ Health check
@app.get("/")
def home():
    return {"status": "API is running 🚀"}

# ✅ Chat endpoint
@app.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        messages = body.get("messages", [])

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {"error": "GROQ API key not found"}

        client = Groq(api_key=api_key)

        all_messages = [
            {
                "role": "system",
                "content": "You are an AI Product Expert."
            }
        ] + messages

        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=all_messages
        )

        reply = response.choices[0].message.content

        return {"reply": reply}

    except Exception as e:
        print("ERROR:", str(e))
        return {"error": str(e)}
    