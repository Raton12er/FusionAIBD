import asyncio, logging, requests
from groq import AsyncGroq
from google import genai
from config import GROQ_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY

logger = logging.getLogger(__name__)
groq_client = AsyncGroq(api_key=GROQ_API_KEY)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

def detect_language(text):
    for ch in text:
        if '\u0980' <= ch <= '\u09FF':
            return "bn"
    return "en"

async def call_groq(question):
    try:
        r = await groq_client.chat.completions.create(
            messages=[{"role": "user", "content": question}],
            model="llama-3.3-70b-versatile",
        )
        return r.choices[0].message.content
    except Exception as e:
        logger.error("Groq: " + str(e))
        return None

def _gemini_sync(question):
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=question,
        )
        return response.text
    except Exception as e:
        logger.error("Gemini: " + str(e))
        return None

async def call_gemini(question):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _gemini_sync, question)

def _openrouter_sync(question):
    try:
        r = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": "Bearer " + OPENROUTER_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek/deepseek-chat:free",
                "messages": [{"role": "user", "content": question}],
            },
            timeout=30,
        )
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error("OpenRouter: " + str(e))
        return None

async def call_openrouter(question):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _openrouter_sync, question)

async def fusion_mode(question, lang):
    results = await asyncio.gather(
        call_groq(question),
        call_gemini(question),
        call_openrouter(question),
        return_exceptions=True,
    )
    g = results[0] if not isinstance(results[0], Exception) else None
    m = results[1] if not isinstance(results[1], Exception) else None
    d = results[2] if not isinstance(results[2], Exception) else None
    available = []
    if g: available.append("Groq: " + g)
    if m: available.append("Gemini: " + m)
    if d: available.append("DeepSeek: " + d)
    if not available:
        return "All AI failed. Try again later."
    if len(available) == 1:
        return available[0]
    lang_instr = "Bengali with English mix" if lang == "bn" else "English"
    prompt = "You are Fusion AI. Combine these 3 AI answers into 1 perfect answer in " + lang_instr + ".\n\nQuestion: " + question + "\n\n" + "\n".join(available)
    try:
        r = await groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        return r.choices[0].message.content
    except Exception as e:
        logger.error("Fusion: " + str(e))
        return available[0]

async def fast_mode(question):
    ans = await call_groq(question)
    return ans or "Groq API failed. Try /fusion or /smart"

async def smart_mode(question):
    ans = await call_gemini(question)
    return ans or "Gemini API failed. Try /fusion or /fast"

async def code_mode(question):
    ans = await call_openrouter("You are an expert programmer. Solve this with explanation:\n" + question)
    return ans or "Code AI failed. Try again."
