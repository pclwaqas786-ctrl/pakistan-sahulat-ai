"""Pakistan Sahulat AI — unofficial concept demo.

America.gov jaisa AI assistant, Pakistan ki sarkari services ke liye.
Backend: Groq free API (key Streamlit secrets me: GROQ_API_KEY).
"""
import json
import re
from pathlib import Path

import requests
import streamlit as st

from core import KB, SYSTEM, build_messages, kb_match

BASE = Path(__file__).parent


def groq_chat(api_key: str, messages, model="openai/gpt-oss-120b", max_tokens=800) -> str:
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model, "messages": messages,
              "max_tokens": max_tokens, "temperature": 0.3},
        timeout=90,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def groq_transcribe(api_key: str, audio_bytes: bytes) -> str:
    r = requests.post(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {api_key}"},
        files={"file": ("voice.wav", audio_bytes, "audio/wav")},
        data={"model": "whisper-large-v3", "language": "ur"},
        timeout=90,
    )
    r.raise_for_status()
    return r.json()["text"].strip()


# ---------- UI ----------
st.set_page_config(page_title="Pakistan Sahulat AI (Concept)", page_icon="🇵🇰", layout="centered")

st.markdown(
    "<div style='background:#fff3cd;border:1px solid #e0c36a;border-radius:10px;"
    "padding:10px 14px;margin-bottom:12px;font-size:14px'>"
    "⚠️ <b>Concept demo</b> — yeh hukumat-e-Pakistan ki <b>official website NAHI</b> hai. "
    "Jawabat maloomat ke liye hain; official links se tasdeeq karo. Koi zaati maloomat (CNIC, OTP) yahan mat likho."
    "</div>",
    unsafe_allow_html=True,
)
st.title("🇵🇰 Pakistan Sahulat AI")
st.caption("Hukumat se jo chahiye, yahin se shuru karo — sawal likho ya bolo, official jawab + official link pao.")

api_key = st.secrets.get("GROQ_API_KEY", "")
if not api_key:
    st.warning("GROQ_API_KEY Streamlit secrets me set karo (App settings → Secrets).")
    st.stop()

if "history" not in st.session_state:
    st.session_state.history = []

SUGGESTED = [
    "Mera CNIC expire ho gaya hai, renew kaise karun?",
    "Passport renew kaise karun?",
    "8171 par paisay check karna hai",
    "Punjab me driving license kaise banay?",
    "Filer kaise banun?",
]
cols = st.columns(3)
for i, q in enumerate(SUGGESTED):
    if cols[i % 3].button(q, key=f"sug{i}"):
        st.session_state.pending = q

audio = st.audio_input("🎤 Bol kar pocho (Urdu/English)")
if audio is not None and st.session_state.get("last_audio") != audio:
    st.session_state["last_audio"] = audio
    with st.spinner("Sun raha hoon..."):
        try:
            st.session_state.pending = groq_transcribe(api_key, audio.getvalue())
        except Exception as e:
            st.error(f"Voice samajh nahi aayi: {e}")

for m in st.session_state.history:
    with st.chat_message("user" if m["role"] == "user" else "assistant"):
        st.markdown(m["content"])

pending = st.session_state.pop("pending", None)
prompt = st.chat_input("Apna sawal likho... masalan: 'B-Form kaise banta hai?'")
query = pending or prompt

if query:
    st.session_state.history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    matches = kb_match(query)
    with st.chat_message("assistant"):
        with st.spinner("Jawab tayyar ho raha hai..."):
            try:
                answer = groq_chat(api_key, build_messages(st.session_state.history[:-1], query, matches))
            except Exception as e:
                answer = f"Maazrat, is waqt jawab nahi de saka ({e}). Dobara koshish karo."
        st.markdown(answer)
    st.session_state.history.append({"role": "assistant", "content": answer})
    st.rerun()

st.divider()
st.caption("Concept: America.gov (US, Sep 2026) se inspired. Sources: NADRA, DGIP, BISP, ECP, FBR, Punjab DLIMS, Sindh Police, K-Electric.")
