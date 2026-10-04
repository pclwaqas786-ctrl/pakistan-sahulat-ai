"""Pure logic for Pakistan Sahulat AI (no Streamlit dependency — testable)."""
import json
from pathlib import Path

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
