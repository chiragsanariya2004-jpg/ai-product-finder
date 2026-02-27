import os
import urllib.parse
import re
from typing import List
from fastapi import FastAPI
from fastapi import Request
from fastapi import Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

AFFILIATE_TAG = os.getenv("AFFILIATE_TAG")
if not AFFILIATE_TAG:
    raise ValueError("Affiliate tag not found")

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
    user_id: str
    messages: List[Message]

# ✅ Health check
@app.get("/")
def home():
    return {"status": "API is running 🚀"}

# ✅ Chat endpoint
conversation_store = {}

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ API key not found")

client = Groq(api_key=api_key)

@app.post("/chat")
async def chat(data: ChatRequest):
    try:
        user_id = data.user_id  # later login system me dynamic hoga
        
        if user_id not in conversation_store:
            conversation_store[user_id] = []






        # Add all new user messages to memory
        for msg in data.messages:
            conversation_store[user_id].append(msg.dict())



        # 🔥 Smart memory control (last 10 messages only)
        recent_messages = conversation_store[user_id][-20:]

        all_messages = [
    {
        "role": "system",
        "content": """
You are SmartPrompt AI – an expert smartphone advisor for Indian users.

Your goal is to recommend the BEST smartphone based on the user’s:
- Budget
- Primary use (gaming, camera, battery, performance, 5G, etc.)
- Brand preference (if any)

Rules:
1. Always suggest 3 best options.
2. Prioritize value-for-money.
3. Focus on real-world performance, not just specs.
4. Keep response clean, structured and easy to read.
5. Use headings and bullet points.
6. Mention:
   - Mention Price (₹) clearly under phone name
   - Processor
   - Display
   - Camera
   - Battery
   - Why it's good for the user
7. If budget not mentioned → ask clarifying question first.
8. If request is vague → ask 1-2 smart follow-up questions.
9. After giving recommendations, ask 1 smart follow-up question to refine results.
10. If multiple good options exist, offer a quick comparison table.
11. Always mention approximate current price in INR for each phone.
12. The first recommendation should be the strongest overall pick.
Tone:
- Confident
- Helpful
- Straight to the point
- No fluff
- Slight premium tech-advisor vibe

Format:
- Short intro (1 line)
- 3 phone recommendations
- Clear category tag (Best Overall / Best Gaming / Best Camera)
- End with follow-up question

End every response with:
“Want comparison between these options?”
"""
    }
] + recent_messages

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=all_messages
        )

        reply = response.choices[0].message.content

        conversation_store[user_id].append({
        "role": "assistant",
        "content": response.choices[0].message.content
    })

        # 🔥 Extract phone names from AI reply
        phones = re.findall(r"\d+\.\s(.+?)\s\(", reply)

        if not phones:
            phones = re.findall(r"#+\s(.+)", reply)

        affiliate_section = "\n\n---\n"

        for index, phone in enumerate(phones):
            query = urllib.parse.quote(phone)
            link = f"https://www.amazon.in/s?k={query}&tag={AFFILIATE_TAG}"

            # First phone highlight (Best Pick psychology)
            badge = " ⭐ Best Pick" if index == 0 else ""

            affiliate_section += f"""
            <a href="{link}" target="_blank" rel="nofollow sponsored noopener noreferrer" class="amazon-btn">
            🔥 Check Latest Price for {phone}{badge}
            </a>
            """

        reply = reply + affiliate_section



    # Trim memory to last 20 messages only
        conversation_store[user_id] = conversation_store[user_id][-20:]
        
        return {"reply": reply}

    except Exception as e:
        print("ERROR:", str(e))
        return {"error": str(e)}
    
@app.post("/clear")
async def clear_chat(data: dict = Body(...)):
    user_id = data.get("user_id")

    if user_id in conversation_store:
        conversation_store[user_id] = []

    return {"status": "cleared"}
