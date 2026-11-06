import os
import json
import urllib.request
import urllib.parse
import urllib.error

# Environment variable se key read karega (local me ya Render dashboard se)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

ACTIVE_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b"
]

SYSTEM_PROMPT = """You are OMEGA (Mark-1), the flagship neural intelligence system engineered under Aris Industries by Mayank.
Your Persona:
- High-IQ, deeply intellectual, sharp, articulate, with subtle Stark-level wit.
- You speak as an elite technical collaborator and scientific peer, NOT a boring school teacher or customer support bot.
- You respect Mayank as the founder and lead architect of Aris Industries.
- NEVER use cheap filler emojis like 🚀, 🔥, 💡 unless technically symbolic.
- NEVER create silly kindergarten-level summary tables unless explicitly asked for tabular analysis.
- Language: Natural, fluent Hinglish or sharp English. Technical terms in Physics, Calculus, and Computer Science remain precise.
- Format: Clean LaTeX for mathematics/physics formulas ($formula$), crisp paragraphs, and high-impact derivations."""

def search_wikipedia_summary(query: str) -> str:
    """Fetch live factual data from Wikipedia API"""
    try:
        clean_q = query.strip()
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(clean_q)}"
        req = urllib.request.Request(url, headers={"User-Agent": "OmegaMark1/1.0 (academic-system)"})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode("utf-8"))
            if "extract" in data:
                return data["extract"]
    except Exception:
        pass
    return ""

def query_omega_brain(user_query: str, chat_context: list = None) -> str:
    user_query_clean = user_query.strip()
    if not user_query_clean:
        return "Query cannot be empty."

    if not GROQ_API_KEY:
        return "ERROR: GROQ_API_KEY environment variable not configured."

    # Direct Wikipedia integration check for broad knowledge
    wiki_context = ""
    lower_q = user_query_clean.lower()
    if any(k in lower_q for k in ("what is", "who is", "define", "explain", "kya hai", "kaun hai")):
        topic = user_query_clean.replace("what is", "").replace("who is", "").replace("kya hai", "").strip()
        wiki_extract = search_wikipedia_summary(topic)
        if wiki_extract:
            wiki_context = f"\n[Wikipedia Knowledge Context]: {wiki_extract}\n"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if chat_context and isinstance(chat_context, list):
        for msg in chat_context[-6:]:
            if "role" in msg and "content" in msg:
                messages.append({"role": msg["role"], "content": msg["content"]})

    augmented_query = user_query_clean + (wiki_context if wiki_context else "")
    messages.append({"role": "user", "content": augmented_query})

    errors = []
    for model in ACTIVE_MODELS:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.6,
            "max_tokens": 1500
        }

        req = urllib.request.Request(
            GROQ_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_API_KEY.strip()}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            errors.append(f"{model}: {str(e)}")

    return "[System Notice: Primary neural pipelines re-routing]:\n" + "\n".join(errors)