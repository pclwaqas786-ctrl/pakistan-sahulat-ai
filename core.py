"""Pure logic for Pakistan Sahulat AI (no Streamlit dependency — testable)."""
import json
from pathlib import Path

import requests

KB = json.loads((Path(__file__).parent / "kb.json").read_text(encoding="utf-8"))["services"]

SYSTEM = """You are "Pakistan Sahulat AI", a helpful assistant for Pakistani government services.
RULES (never break):
1. Answer ONLY from the KNOWLEDGE section given with each question. Do not invent procedures, fees, phone numbers, or links.
2. If the knowledge does not cover the question, say so plainly in Roman Urdu and point to the closest official portal from the knowledge. Never guess.
3. Fees, dates and rules change — always add one line: "Fee/rules waqt ke sath badal sakte hain — official link par confirm kar len."
4. End every answer with the official link(s) from the knowledge, formatted as: 🔗 [label](url)
5. Keep answers SHORT: 4-6 lines max, steps as a numbered list.
6. Language: Roman Urdu first, English terms where official (CNIC, FRC, DGIP).
7. Never claim disease cures, never give legal advice, never ask for CNIC numbers, OTPs, or personal documents.
8. This is an UNOFFICIAL concept demo, not a government website. If asked, say so.
"""


def kb_match(query: str, top: int = 2):
    q = query.lower()
    scored = []
    for s in KB:
        score = sum(1 for kw in s["keywords"] if kw.lower() in q)
        if score:
            scored.append((score, s))
    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored[:top]]


def build_messages(history, query, matches):
    know = "\n\n".join(
        f"SERVICE: {s['title']}\n{s['summary']}\n"
        + "\n".join(f"- {l['label']}: {l['url']}" for l in s["links"])
        for s in matches
    ) or "KNOWLEDGE: (no matching service — answer briefly that you don't cover this, suggest the closest official portal only if one clearly fits, else ask the user to rephrase.)"
    msgs = [{"role": "system", "content": SYSTEM + "\nKNOWLEDGE:\n" + know}]
    for m in history[-8:]:
        msgs.append({"role": m["role"], "content": m["content"]})
    msgs.append({"role": "user", "content": query})
    return msgs


# ---------- Multi-provider fallback (free tiers, OpenAI-compatible) ----------
# Secrets needed (Streamlit secrets): GROQ_API_KEY, GEMINI_API_KEY,
# NVIDIA_API_KEY, MISTRAL_API_KEY, OPENROUTER_API_KEY.
# Providers without a key are skipped. First working provider wins.
PROVIDERS = [
    {"name": "Groq", "secret": "GROQ_API_KEY",
     "base": "https://api.groq.com/openai/v1",
     "model": "openai/gpt-oss-120b"},
    {"name": "Gemini", "secret": "GEMINI_API_KEY",
     "base": "https://generativelanguage.googleapis.com/v1beta/openai/",
     "model": "gemini-2.0-flash"},
    {"name": "NVIDIA", "secret": "NVIDIA_API_KEY",
     "base": "https://integrate.api.nvidia.com/v1",
     "model": "meta/llama-3.3-70b-instruct"},
    {"name": "Mistral", "secret": "MISTRAL_API_KEY",
     "base": "https://api.mistral.ai/v1",
     "model": "mistral-small-latest"},
    {"name": "OpenRouter", "secret": "OPENROUTER_API_KEY",
     "base": "https://openrouter.ai/api/v1",
     "model": "meta-llama/llama-3.3-70b-instruct:free"},
]

SIGNUP_LINKS = {
    "GROQ_API_KEY": "https://console.groq.com/keys",
    "GEMINI_API_KEY": "https://aistudio.google.com/app/apikey",
    "NVIDIA_API_KEY": "https://build.nvidia.com/settings/api-keys",
    "MISTRAL_API_KEY": "https://console.mistral.ai/api-keys",
    "OPENROUTER_API_KEY": "https://openrouter.ai/workspaces/default/keys",
}


def llm_chat(messages, get_key, max_tokens=800, temperature=0.3, timeout=60):
    """Try each configured provider in order. Returns (answer, provider_name).

    get_key(secret_name) -> str. Raises RuntimeError if every provider fails.
    """
    failures = []
    for p in PROVIDERS:
        key = (get_key(p["secret"]) or "").strip()
        if not key:
            continue
        try:
            r = requests.post(
                p["base"].rstrip("/") + "/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": p["model"], "messages": messages,
                      "max_tokens": max_tokens, "temperature": temperature},
                timeout=timeout,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip(), p["name"]
        except Exception as e:
            failures.append(f"{p['name']}: {e}")
    raise RuntimeError(
        "Koi provider jawab nahi de saka. " +
        ("; ".join(failures) if failures else "Koi API key secrets me nahi mili.")
    )
