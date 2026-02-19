import os
from typing import List
from fastapi import FastAPI
from fastapi import Request
from fastapi import Body
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
conversation_store = {}

@app.post("/chat")
async def chat(data: ChatRequest):
    try:
        user_id = "default_user"  # later login system me dynamic hoga
        
        if user_id not in conversation_store:
            conversation_store[user_id] = []

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {"error": "GROQ API key not found"}

        client = Groq(api_key=api_key)

        # Add new user messages to memory
        new_message = data.messages[0]

        # Add new user message to memory
        conversation_store[user_id].append(new_message)

        # 🔥 Smart memory control (last 10 messages only)
        recent_messages = conversation_store[user_id][-20:]

        all_messages = [
            {
                "role": "system",
                "content": "You are an AI Product Expert. Always use previous conversation context to understand references like 'this', 'that', or 'translate this'."
            }
        ] + [msg.dict() for msg in recent_messages]

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=all_messages
        )

        reply = response.choices[0].message.content

        # Save assistant reply to memory
        conversation_store[user_id].append({
            "role": "assistant",
            "content": reply
        })

        return {"reply": reply}

    except Exception as e:
        print("ERROR:", str(e))
        return {"error": str(e)}
    