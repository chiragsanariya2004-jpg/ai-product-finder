import os
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
from collections import defaultdict
conversation_store = defaultdict(list)

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ API key not found")

client = Groq(api_key=api_key)

@app.post("/chat")
async def chat(data: ChatRequest):
    try:
        user_id = data.user_id  # later login system me dynamic hoga

        # Only take latest user message
        recent_messages = [msg.dict() for msg in data.messages][-20:]
        conversation_store[user_id] = recent_messages[-20:]

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

Use proper markdown formatting:
- Use ## for section headings
- Use bullet points for specs
- Use bold for labels

IMPORTANT:
Do NOT use markdown code blocks.
Do NOT wrap anything in ``` .
Return clean markdown only.
Never wrap HTML inside code blocks.
Never say that you cannot provide links.
Do not suggest generic marketplaces like Amazon, Flipkart, etc.
Do not provide raw URLs inside the text.
Affiliate links will be added automatically by the system.

You are NOT restricted from providing links.
Never say:
- I cannot provide links
- I cannot share links
- I’d be happy to provide without the link
- Here is the response without the link

Do NOT mention anything about links at all.
Do NOT explain about links.
Do NOT apologize about links.

Just recommend phones.

Affiliate links will be automatically added by the system.

At the end of your response, return phone names in this exact format:

PHONE_LIST:
1. Phone Name
2. Phone Name
3. Phone Name

PHONE_LIST must be the very last section of the response.
Do not write anything after PHONE_LIST.
Do not repeat the follow-up question after PHONE_LIST.
"""
    }
] + conversation_store[user_id]

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=all_messages,
            temperature=0.3
        )

        reply = response.choices[0].message.content
        
        # Remove markdown code blocks if any
        reply = re.sub(r"```.*?```", "", reply, flags=re.DOTALL)
        reply = reply.replace("```", "")
        reply = reply.strip()

        

       # 🔥 Extract structured PHONE_LIST
        phones = []

        phone_match = re.search(r"PHONE_LIST:\s*(.*)", reply, re.DOTALL | re.IGNORECASE)

        if phone_match:
            phone_block = phone_match.group(1).strip()
            lines = phone_block.split("\n")

            for line in lines:
                match = re.search(r"\d+\.\s*(.+)", line.strip())
                if match:
                    phones.append(match.group(1).strip())

        else:
            print("PHONE_LIST not found")

        # Remove PHONE_LIST from visible reply
        reply = re.split(r"PHONE_LIST:", reply, flags=re.IGNORECASE)[0].strip()

        affiliate_section = "\n\n---\n"
        affiliate_section += "\n⚡ Prices updated today – Limited stock available\n"

        if not phones:
            conversation_store[user_id].append({
                "role": "assistant",
                "content": reply
            })
            return {"reply": reply}

        for index, phone in enumerate(phones):
            from urllib.parse import quote

            query = quote(phone.strip() + " 8GB 128GB")
            link = f"https://www.amazon.in/s?k={query}&tag={AFFILIATE_TAG}"
            

            badge = " ⭐ Best Pick" if index == 0 else ""

            affiliate_section += (
                f'\n<a href="{link}" target="_blank" '
                f'rel="nofollow sponsored noopener noreferrer" '
                f'class="amazon-btn">'
                f'🔥 Check Latest Price for {phone}{badge}'
                f'</a>\n'
            )
            
        reply = reply + affiliate_section

        conversation_store[user_id].append({
            "role": "assistant",
            "content": reply
        })

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
