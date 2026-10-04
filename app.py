"""Pakistan Sahulat AI — unofficial concept demo.

America.gov jaisa AI assistant, Pakistan ki sarkari services ke liye.
Backend: Groq free API (key Streamlit secrets me: GROQ_API_KEY).
Tabs: Assistant (chat+PDF+voice) | Live Flights | Hajj & Umrah | Service Directory
"""
from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as components

from core import KB, build_messages, kb_match

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

BASE = Path(__file__).parent

st.set_page_config(page_title="Pakistan Sahulat AI (Concept)", page_icon="🇵🇰", layout="wide")

st.markdown(
    "<div style='background:#fff3cd;border:1px solid #e0c36a;border-radius:10px;"
    "padding:10px 14px;margin-bottom:12px;font-size:14px'>"
    "⚠️ <b>Concept demo</b> — yeh hukumat-e-Pakistan ki <b>official website NAHI</b> hai. "
    "Jawabat maloomat ke liye hain; official links se tasdeeq karo. Koi zaati maloomat (CNIC, OTP) yahan mat likho."
    "</div>",
    unsafe_allow_html=True,
)
st.title("🇵🇰 Pakistan Sahulat AI")
st.caption("Hukumat se jo chahiye, yahin se shuru karo.")

api_key = st.secrets.get("GROQ_API_KEY", "")
if not api_key:
    st.warning("GROQ_API_KEY Streamlit secrets me set karo (App settings → Secrets).")
    st.stop()


def groq_chat(messages, model="openai/gpt-oss-120b", max_tokens=800) -> str:
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model, "messages": messages,
              "max_tokens": max_tokens, "temperature": 0.3},
        timeout=90,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def groq_transcribe(audio_bytes: bytes) -> str:
    r = requests.post(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {api_key}"},
        files={"file": ("voice.wav", audio_bytes, "audio/wav")},
        data={"model": "whisper-large-v3", "language": "ur"},
        timeout=90,
    )
    r.raise_for_status()
    return r.json()["text"].strip()


tab_chat, tab_flights, tab_hajj, tab_dir = st.tabs(
    ["💬 Assistant", "✈️ Live Flights", "🕋 Hajj & Umrah", "📚 Service Directory"]
)

# ================= TAB 1: CHAT =================
with tab_chat:
    if "history" not in st.session_state:
        st.session_state.history = []

    with st.expander("📄 Sarkari letter / form samjhao (PDF upload)"):
        pdf = st.file_uploader("PDF upload karo — masalan BISP letter, bill, ya form", type=["pdf"])
        if pdf and PdfReader:
            try:
                reader = PdfReader(pdf)
                text = "\n".join((p.extract_text() or "") for p in reader.pages)[:6000]
                st.session_state["pdf_text"] = text
                st.success(f"PDF parh liya ({len(reader.pages)} pages). Ab neeche sawal likho — masalan 'is letter ka matlab kya hai?'")
            except Exception as e:
                st.error(f"PDF nahi parh saka: {e}")
        elif pdf:
            st.error("PDF support install nahi (pypdf).")

    SUGGESTED = [
        "Mera CNIC expire ho gaya hai, renew kaise karun?",
        "Passport renew kaise karun?",
        "8171 par paisay check karna hai",
        "Hajj 2027 ki second qist kab jama hogi?",
        "Filer kaise banun?",
        "Driving license (Punjab) kaise banay?",
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
                st.session_state.pending = groq_transcribe(audio.getvalue())
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
        pdf_text = st.session_state.get("pdf_text", "")
        if pdf_text:
            matches, extra = [], ("DOCUMENT TEXT (user ka uploaded sarkari letter/form):\n" + pdf_text
                + "\n\nIs document ki bunyad par sawal ka jawab do. Jo document me na ho, wahan KB use karo.")
        else:
            matches, extra = kb_match(query), ""
        with st.chat_message("assistant"):
            with st.spinner("Jawab tayyar ho raha hai..."):
                try:
                    msgs = build_messages(st.session_state.history[:-1], query, matches)
                    if extra:
                        msgs[0]["content"] += "\n" + extra
                    answer = groq_chat(msgs)
                except Exception as e:
                    answer = f"Maazrat, is waqt jawab nahi de saka ({e}). Dobara koshish karo."
            st.markdown(answer)
        st.session_state.history.append({"role": "assistant", "content": answer})
        st.rerun()

# ================= TAB 2: LIVE FLIGHTS =================
with tab_flights:
    st.subheader("✈️ Pakistan ke upar live flights")
    st.caption("Real-time ADS-B data (OpenSky Network) — 60 second me refresh hota hai.")

    @st.cache_data(ttl=60)
    def fetch_flights():
        r = requests.get(
            "https://opensky-network.org/api/states/all",
            params={"lamin": 23, "lomin": 60, "lamax": 38, "lomax": 78},
            timeout=25,
        )
        r.raise_for_status()
        flights = []
        for s in r.json().get("states") or []:
            if s[5] is None or s[6] is None:
                continue
            flights.append({
                "callsign": (s[1] or "N/A").strip(),
                "country": s[2] or "?",
                "lat": round(s[6], 3), "lon": round(s[5], 3),
                "alt_ft": int(s[7] * 3.281) if s[7] else 0,
                "speed_kmh": int(s[9] * 3.6) if s[9] else 0,
                "heading": int(s[10]) if s[10] else 0,
            })
        return flights

    try:
        flights = fetch_flights()
        st.success(f"Is waqt **{len(flights)}** flights is region (Pakistan + ird-gird) me live track ho rahi hain.")
        markers = "\n".join(
            f"L.marker([{f['lat']},{f['lon']}],{{icon:L.divIcon({{className:'',"
            f"html:'<div style=\"transform:rotate({f['heading']}deg);font-size:20px\">✈️</div>',"
            f"iconSize:[24,24],iconAnchor:[12,12]}})}})"
            f".addTo(map).bindPopup(\"<b>{f['callsign']}</b><br>{f['country']}<br>"
            f"{f['alt_ft']:,} ft · {f['speed_kmh']} km/h\");"
            for f in flights[:150]
        )
        html = f"""<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <div id="m" style="height:480px;border-radius:12px"></div>
        <script>var map=L.map('m').setView([30.0,69.0],5);
        L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
        {{attribution:'© OpenStreetMap'}}).addTo(map);{markers}</script>"""
        components.html(html, height=500)
        if st.checkbox("Flight list dikhao", value=False):
            st.dataframe(
                [{"Callsign": f["callsign"], "Country": f["country"],
                  "Altitude (ft)": f["alt_ft"], "Speed (km/h)": f["speed_kmh"]}
                 for f in flights[:100]],
                use_container_width=True,
            )
    except Exception as e:
        st.warning(f"Live data is waqt nahi mil saka ({e}). Thori der baad refresh karo.")

# ================= TAB 3: HAJJ & UMRAH =================
with tab_hajj:
    st.subheader("🕋 Hajj 2027 — Government Scheme (taza tareen)")
    st.caption("Last updated: 4 Oct 2026 · Source: Ministry of Religious Affairs announcements (news reports)")
    st.error("⏰ **Second instalment: 5 – 20 October 2026** — Pak Hajj app / Digital Hajj Portal par jama karo. "
             "Pehle **medical fitness certificate upload karna LAZMI** hai, warna payment nahi hogi. "
             "Deadline miss = application **cancel** (jama raqam refund ho jayegi).")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**✅ Karna hai**\n- Medical certificate upload karo (Pak Hajj app)\n"
                    "- 5–20 Oct ke darmiyan second qist jama karo\n- Payment sirf app/portal se")
    with c2:
        st.markdown("**🚫 Mat karna**\n- Last day ka wait mat karo\n- Kisi agent ko paise/OTP mat do\n"
                    "- Bina medical upload ke payment try mat karo")
    st.info("👷 **Labour quota:** companies apne low-income workers ko sponsor kar sakti hain — "
            "applications **10 Oct 2026** tak, first-come-first-served, sirf hajj.mora.gov.pk par. "
            "Employer apply karega aur employer hi pay karega.")
    st.markdown("🔗 [Ministry of Religious Affairs](https://mora.gov.pk) · "
                "🔗 [Hajj portal](https://hajj.mora.gov.pk)")
    st.divider()
    st.subheader("Umrah")
    st.write("Umrah private operators ke through hota hai. **Advance payment se pehle** operator Ministry "
             "ke approved list me check karo (mora.gov.pk). Bina license wale agent ko paise mat do.")
    st.caption("News sources: PakEra, Abb Takk, UrduPoint, 24 News HD (1–3 Oct 2026)")

# ================= TAB 4: DIRECTORY =================
with tab_dir:
    st.subheader("📚 Sarkari Services Directory")
    cats = {}
    for s in KB:
        cats.setdefault(s.get("cat", "Other"), []).append(s)
    for cat in sorted(cats):
        with st.expander(f"**{cat}** ({len(cats[cat])})"):
            for s in cats[cat]:
                st.markdown(f"**{s['title']}**")
                st.write(s["summary"])
                for l in s["links"]:
                    st.markdown(f"🔗 [{l['label']}]({l['url']})")
                st.divider()

st.divider()
st.caption("Concept: America.gov (US, Sep 2026) se inspired · Unofficial demo · Sources: NADRA, DGIP, BISP, ECP, FBR, MoRA, PLRA, Excise, EOBI, BEOE, SNGPL, SSGC, Sindh Police, K-Electric · Flights: OpenSky Network")
