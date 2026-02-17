import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Product Expert API")

# ✅ CORS (Vercel frontend ko allow karega)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # production me specific domain dal sakte ho
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Request Model
class ChatRequest(BaseModel):
    message: str


# ✅ Health check route (Render ke liye important)
@app.get("/")
def home():
    return {"status": "API is running 🚀"}


# ✅ Chat endpoint
@app.post("/chat")
def chat(request: ChatRequest):
    try:
        client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )

        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI Product Expert. Help users choose the best products."
                },
                {
                    "role": "user",
                    "content": request.message
                }
            ]
        )

        reply = response.choices[0].message.content

        return {"reply": reply}

    except Exception as e:
        return {"error": str(e)}
