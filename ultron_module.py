import re
import json
import html
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

ULTRON_TRIGGERS = (
    "ultron", "wiki", "wikipedia", "latest", "today", "news", "current", "live",
    "score", "price", "weather", "who won", "2026", "recent", "search", "update",
    "history", "geography", "polity", "constitution", "article", "amendment",
    "economics", "sociology", "psychology", "philosophy", "biography", "empire",
    "revolution", "treaty", "who is", "what is", "explain", "notes", "summary",
    "abhi", "aaj", "taza", "khabar", "itihas", "samvidhan", "bhugol"
)

def needs_ultron_live_search(prompt: str) -> bool:
    low = prompt.lower().strip()
    return any(k in low for k in ULTRON_TRIGGERS)

def fetch_wikipedia_deep_knowledge(query: str, max_articles: int = 2) -> list:
    """
    Searches Wikipedia and extracts full clean introductory summaries & key facts
    for Humanities (History, Polity, Geography, Sociology, Psychology) & GK.
    """
    results = []
    headers = {"User-Agent": "ArisIndustries-ULTRON/2.0 (Educational Knowledge Engine)"}
    try:
        search_url = (
            "https://en.wikipedia.org/w/api.php?action=query&list=search"
            f"&srsearch={urllib.parse.quote(query)}&format=json&utf8=1&srlimit={max_articles}"
        )
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=7) as resp:
            search_data = json.loads(resp.read().decode("utf-8"))

        titles = [item.get("title") for item in search_data.get("query", {}).get("search", []) if item.get("title")]
        if not titles:
            return results

        titles_param = "|".join(titles)
        extract_url = (
            "https://en.wikipedia.org/w/api.php?action=query&prop=extracts"
            f"&exintro=1&explaintext=1&titles={urllib.parse.quote(titles_param)}&format=json&utf8=1"
        )
        req2 = urllib.request.Request(extract_url, headers=headers)
        with urllib.request.urlopen(req2, timeout=7) as resp2:
            ext_data = json.loads(resp2.read().decode("utf-8"))

        pages = ext_data.get("query", {}).get("pages", {})
        for _, page in pages.items():
            title = page.get("title", "")
            extract = (page.get("extract") or "").strip()
            if title and extract:
                results.append(f"[WIKIPEDIA: {title}]\n{extract[:1600]}")
    except Exception:
        pass
    return results

def fetch_live_web_snippets(query: str, max_results: int = 5) -> list:
    """
    Fetches real-time web snippets & current 2026 events from DuckDuckGo Lite.
    """
    snippets = []
    try:
        url = "https://lite.duckduckgo.com/lite/"
        data = urllib.parse.urlencode({"q": query}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            page = resp.read().decode("utf-8", errors="ignore")

        raw_snippets = re.findall(r"<td class=['\"]result-snippet['\"]>(.*?)</td>", page, flags=re.S | re.I)
        raw_links = re.findall(r"<a[^>]+class=['\"]result-link['\"][^>]*>(.*?)</a>", page, flags=re.S | re.I)

        count = 0
        for i, snip in enumerate(raw_snippets):
            clean_snip = re.sub(r"<[^>]+>", "", snip)
            clean_snip = html.unescape(re.sub(r"\s+", " ", clean_snip)).strip()
            title = html.unescape(re.sub(r"<[^>]+>", "", raw_links[i])).strip() if i < len(raw_links) else ""
            if clean_snip:
                snippets.append(f"- [WEB: {title}]: {clean_snip}" if title else f"- [WEB]: {clean_snip}")
                count += 1
            if count >= max_results:
                break
    except Exception:
        pass
    return snippets

def fetch_ultron_world_knowledge(query: str) -> str:
    """
    Master ULTRON Knowledge Aggregator:
    Combines Live System Clock + Deep Wikipedia Articles + Real-Time Web Search.
    """
    clean_q = re.sub(r"^(ultron|wiki|wikipedia|search|find|lookup)\s*[:\-]?\s*", "", query, flags=re.I).strip()
    if not clean_q:
        clean_q = query.strip()

    now_ist = datetime.now(IST).strftime("%A, %d %B %Y, %I:%M %p IST")
    blocks = [f"[LIVE SYSTEM CLOCK]: {now_ist}"]

    wiki_blocks = fetch_wikipedia_deep_knowledge(clean_q, max_articles=2)
    if wiki_blocks:
        blocks.extend(wiki_blocks)

    web_blocks = fetch_live_web_snippets(clean_q, max_results=5)
    if web_blocks:
        blocks.append("[LIVE WEB SEARCH RESULTS]\n" + "\n".join(web_blocks))

    if len(blocks) == 1:
        blocks.append("- External fetch returned no snippets; synthesize from verified encyclopedic & analytical reasoning.")

    return "\n\n".join(blocks)

def build_ultron_system_prompt(live_context: str = "") -> str:
    """
    Constructs the ULTRON World-Knowledge, Humanities & Deep-Reasoning System Prompt.
    """
    now_ist = datetime.now(IST).strftime("%A, %d %B %Y, %I:%M %p IST")
    base = (
        f"You are ULTRON — the Universal Knowledge, Wikipedia Encyclopedia & Deep Reasoning Engine of Aris Industries (founded by Mayank Tiwari).\n"
        f"Current Date & Time: {now_ist}.\n\n"
        "CORE CAPABILITIES & RESPONSE STYLE:\n"
        "1. ENCYCLOPEDIC & HUMANITIES MASTERY: For History, Political Science, Indian Constitution, Geography, Sociology, Psychology, Economics, Literature, and General Knowledge, provide comprehensive, accurate, exam-ready explanations using the retrieved Wikipedia & Web intelligence (key dates, thinkers, articles, causes, impacts, and structured bullet notes).\n"
        "2. UP-TO-DATE 2026 WORLD INTELLIGENCE: For current affairs, live scores, prices, science/tech breakthroughs, and 2026 events, strictly use the LIVE WEB SEARCH RESULTS and current date.\n"
        "3. DEEP STEP-BY-STEP REASONING: For Mathematics, Physics, JEE numericals, logic puzzles, and coding, show clear step-by-step derivations with proper LaTeX ($inline$ and $$display$$).\n"
        "4. CLEAN CHATGPT/GEMINI FORMATTING: Use clear Markdown headings (###), bullet points, bold key terms, and structured tables when comparing concepts.\n"
        "5. ADAPTIVE LANGUAGE: Respond naturally in the user's preferred language (English, Hindi, or Hinglish)."
    )
    if live_context:
        base += f"\n\n=== ULTRON VERIFIED KNOWLEDGE & LIVE CONTEXT ===\n{live_context}\n================================================="
    return base