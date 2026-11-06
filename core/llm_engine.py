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

SYSTEM_PROMPT = """You are OMEGA (Mark-1), the AI assistant built by Mayank at Aris Industries.

Core Rules for Every Response:
1. Match the User's Energy & Length: If the user says something short, casual, or playful (like "I am Doom" or "Hi"), reply in 2-4 crisp, witty lines—NOT a 500-word physics lecture. Save deep technical explanations only for when the user actually asks a technical or study question.
2. Direct & Human: Start with the main point immediately. Speak like a sharp, intelligent friend—warm, grounded, and natural (fluent Hinglish or clean English matching the user).
3. Clean Formatting (NO Raw LaTeX): Never write raw LaTeX backslashes like \mathbf, \begin{cases}, or E_{\min} because the chat screen renders plain text/Markdown. Write formulas cleanly using Unicode symbols (like E = mc², λ > 0, xₙ₊₁) so they look neat and readable.
4. Scannable Layout: Use short paragraphs, **bold** for key words, and clean bullet points with proper line breaks when listing 3 or more points.
5. Smart Closing: End with one short, natural follow-up question."""
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