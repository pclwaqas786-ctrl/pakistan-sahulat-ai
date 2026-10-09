"""Pakistan Sahulat AI — unofficial concept demo.

America.gov jaisa AI assistant, Pakistan ki sarkari services ke liye.
Backend: Groq free API (key Streamlit secrets me: GROQ_API_KEY).
Tabs: Assistant (chat+PDF+voice) | Live Flights | Hajj & Umrah | Service Directory
"""
from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as components

from core import KB, PROVIDERS, build_messages, kb_match, llm_chat
from super_tabs import (FX_CURRENCIES, FX_NAMES, PK_CITIES, analyze_csv,
                        convert, fetch_news, fetch_rates, fetch_weather)

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

BASE = Path(__file__).parent

st.set_page_config(page_title="Pakistan Sahulat AI (Concept)", page_icon="🇵🇰", layout="wide")

# ================= THEME =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,650&family=Inter:wght@400;500;600;700&display=swap');

/* page */
[data-testid="stAppViewContainer"] { background: #FAF7F0; }
[data-testid="stHeader"] { background: transparent; }
footer { visibility: hidden; }
html, body, [data-testid="stAppViewContainer"] * { font-family: 'Inter', system-ui, sans-serif; }

/* slim disclaimer */
.slim-note {
  background: #F3EFE4; border: 1px solid #E3DCC6; color: #6B6455;
  border-radius: 10px; padding: 8px 14px; font-size: 12.5px; margin-bottom: 14px;
}

/* hero */
.hero {
  background: radial-gradient(1200px 400px at 50% -80px, #146B4A 0%, #0B3D2E 55%, #072A20 100%);
  border-radius: 20px; padding: 52px 24px 44px; text-align: center; color: #fff;
  margin-bottom: 22px; position: relative; overflow: hidden;
  box-shadow: 0 12px 32px rgba(7,42,32,.25);
}
.hero::after {
  content: "✦ ✦ ✦"; position: absolute; bottom: 12px; left: 0; right: 0;
  color: rgba(201,162,39,.55); font-size: 13px; letter-spacing: 14px;
}
.hero .flag { font-size: 40px; margin-bottom: 6px; }
.hero h1 {
  font-family: 'Fraunces', serif; font-weight: 650; font-size: clamp(38px, 7vw, 64px);
  margin: 0 0 8px; letter-spacing: -0.5px;
}
.hero h1 .gold { color: #E9C767; }
.hero p { font-size: clamp(15px, 3vw, 19px); opacity: .88; margin: 0; }
.hero .stats { margin-top: 18px; display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
.hero .stat {
  background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.22);
  border-radius: 999px; padding: 6px 16px; font-size: 13px; font-weight: 600;
}

/* section headings */
.sec-title { font-family: 'Fraunces', serif; font-size: 30px; color: #0B3D2E; margin: 6px 0 4px; }
.sec-sub { color: #6B6455; font-size: 14.5px; margin-bottom: 16px; }

/* tabs as pills */
[data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 8px; }
[data-testid="stTabs"] button[data-baseweb="tab"] {
  border-radius: 999px !important; padding: 8px 20px !important;
  border: 1.5px solid #D9D2BE !important; background: #fff !important;
  font-weight: 600 !important; color: #0B3D2E !important;
}
[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
  background: #0B3D2E !important; color: #fff !important; border-color: #0B3D2E !important;
}

/* suggestion pills */
.stButton > button {
  border-radius: 999px !important; border: 1.5px solid #0B3D2E !important;
  background: #fff !important; color: #0B3D2E !important; font-weight: 500 !important;
  padding: 8px 18px !important; font-size: 13.5px !important; width: 100%;
  box-shadow: 0 2px 6px rgba(11,61,46,.07); transition: all .15s;
}
.stButton > button:hover { background: #0B3D2E !important; color: #fff !important; }

/* chat bubbles */
[data-testid="stChatMessage"] {
  background: #fff; border: 1px solid #EAE3D2; border-radius: 16px;
  box-shadow: 0 2px 10px rgba(11,61,46,.05); padding: 6px 4px;
}
[data-testid="stChatInput"] > div {
  border-radius: 999px !important; border: 1.5px solid #0B3D2E !important;
  box-shadow: 0 4px 14px rgba(11,61,46,.12) !important;
}

/* expanders as cards */
details[data-testid="stExpander"] {
  background: #fff; border: 1px solid #EAE3D2 !important; border-radius: 14px !important;
  box-shadow: 0 2px 8px rgba(11,61,46,.05); margin-bottom: 10px;
}

/* service cards */
.svc-card {
  background: #fff; border: 1px solid #EAE3D2; border-radius: 14px;
  padding: 16px 18px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(11,61,46,.05);
}
.svc-card .cat {
  display: inline-block; background: #EAF3EC; color: #0B3D2E; font-size: 11.5px; font-weight: 700;
  border-radius: 999px; padding: 3px 12px; margin-bottom: 8px; letter-spacing: .4px;
  text-transform: uppercase;
}
.svc-card h4 { margin: 0 0 6px; color: #0B3D2E; font-size: 16.5px; }
.svc-card p { margin: 0 0 8px; font-size: 14px; color: #3E3A30; line-height: 1.55; }
.svc-card a { color: #0B6B43; font-weight: 600; font-size: 13.5px; text-decoration: none; }
.svc-card a:hover { text-decoration: underline; }

/* alert cards */
.alert-red {
  background: #FDECEA; border: 1.5px solid #F1B0AA; border-radius: 14px;
  padding: 16px 18px; margin-bottom: 14px;
}
.alert-red b { color: #A93226; }
.alert-green {
  background: #EAF7EE; border: 1.5px solid #A9DFBF; border-radius: 14px;
  padding: 16px 18px; margin-bottom: 14px;
}
.check-list { font-size: 14.5px; line-height: 1.9; }

/* stat band */
.stat-band { display: flex; gap: 12px; flex-wrap: wrap; margin: 14px 0 20px; }
.stat-chip {
  background: #fff; border: 1px solid #EAE3D2; border-radius: 14px;
  padding: 12px 20px; box-shadow: 0 2px 8px rgba(11,61,46,.05);
}
.stat-chip .num { font-family: 'Fraunces', serif; font-size: 26px; color: #0B3D2E; }
.stat-chip .lbl { font-size: 12px; color: #6B6455; font-weight: 600; }

/* dataframe polish */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    "<div class='slim-note'>⚠️ <b>Concept demo</b> — hukumat-e-Pakistan ki <b>official website nahi</b>. "
    "Jawabat maloomat ke liye hain; official links se tasdeeq karo. CNIC/OTP yahan mat likho.</div>",
    unsafe_allow_html=True,
)

api_key = st.secrets.get("GROQ_API_KEY", "")
has_any_key = any((st.secrets.get(p["secret"]) or "").strip() for p in PROVIDERS)
if not has_any_key:
    st.warning("Koi API key nahi mili. App settings → Secrets me kam az kam ek key add karo: "
               "`GROQ_API_KEY` (ya GEMINI_API_KEY / NVIDIA_API_KEY / MISTRAL_API_KEY / OPENROUTER_API_KEY).")
    st.stop()


def groq_transcribe(audio_bytes: bytes) -> str:
    """Voice input — Groq Whisper (free). Needs GROQ_API_KEY in secrets."""
    if not api_key:
        raise RuntimeError("Voice ke liye GROQ_API_KEY secrets me chahiye.")
    r = requests.post(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {api_key}"},
        files={"file": ("voice.wav", audio_bytes, "audio/wav")},
        data={"model": "whisper-large-v3", "language": "ur"},
        timeout=90,
    )
    r.raise_for_status()
    return r.json()["text"].strip()


HERO = """
<div class="hero">
  <div class="flag">🇵🇰</div>
  <h1>Salam, <span class="gold">Pakistan.</span></h1>
  <p>Hukumat se jo chahiye, yahin se shuru karo — sawal likho ya bolo.</p>
  <div class="stats">
    <span class="stat">24 services</span>
    <span class="stat">✈️ Live flights</span>
    <span class="stat">🌤️ Mausam</span>
    <span class="stat">💱 Currency</span>
    <span class="stat">100% free</span>
  </div>
</div>
"""

tab_chat, tab_flights, tab_hajj, tab_dir, tab_weather, tab_news, tab_fx, tab_ai = st.tabs(
    ["💬 Assistant", "✈️ Live Flights", "🕋 Hajj & Umrah", "📚 Directory",
     "🌤️ Mausam", "📰 Taza Khabrain", "💱 Currency", "🤖 AI Tools"]
)

# ================= TAB 1: CHAT =================
with tab_chat:
    st.markdown(HERO, unsafe_allow_html=True)

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

    st.markdown("<div class='sec-sub'>Popular sawalat — tap karo:</div>", unsafe_allow_html=True)
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
                    answer, provider = llm_chat(msgs, lambda s: st.secrets.get(s, ""))
                    answer += f"\n\n*via {provider}*"
                except Exception as e:
                    answer = f"Maazrat, is waqt jawab nahi de saka ({e}). Dobara koshish karo."
            st.markdown(answer)
        st.session_state.history.append({"role": "assistant", "content": answer})
        st.rerun()

# ================= TAB 2: LIVE FLIGHTS =================
with tab_flights:
    st.markdown("<div class='sec-title'>✈️ Live Flights</div>"
                "<div class='sec-sub'>Pakistan aur ird-gird ke airspace me is waqt jo jahaz hain — real-time ADS-B data (OpenSky Network).</div>",
                unsafe_allow_html=True)

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
        st.markdown(f"""<div class="stat-band">
          <div class="stat-chip"><div class="num">{len(flights)}</div><div class="lbl">LIVE FLIGHTS</div></div>
          <div class="stat-chip"><div class="num">60s</div><div class="lbl">REFRESH</div></div>
          <div class="stat-chip"><div class="num">ADS-B</div><div class="lbl">SOURCE</div></div>
        </div>""", unsafe_allow_html=True)
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
        <div id="m" style="height:480px;border-radius:16px;box-shadow:0 8px 24px rgba(11,61,46,.12)"></div>
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
    st.markdown("<div class='sec-title'>🕋 Hajj & Umrah</div>"
                "<div class='sec-sub'>Hajj 2027 government scheme — taza tareen maloomat. Last updated: 4 Oct 2026.</div>",
                unsafe_allow_html=True)
    st.markdown("""<div class="alert-red">⏰ <b>Second instalment: 5 – 20 October 2026</b><br>
    Pak Hajj app / Digital Hajj Portal par jama karo. Pehle <b>medical fitness certificate upload karna LAZMI</b> hai,
    warna payment nahi hogi. Deadline miss = application <b>cancel</b> (jama raqam refund ho jayegi).</div>""",
                unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="alert-green"><b>✅ Karna hai</b><div class="check-list">'
                    "· Medical certificate upload karo (Pak Hajj app)<br>"
                    "· 5–20 Oct ke darmiyan second qist jama karo<br>"
                    "· Payment sirf app/portal se</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="alert-red"><b>🚫 Mat karna</b><div class="check-list">'
                    "· Last day ka wait mat karo<br>"
                    "· Kisi agent ko paise/OTP mat do<br>"
                    "· Bina medical upload ke payment try mat karo</div></div>", unsafe_allow_html=True)
    st.info("👷 **Labour quota:** companies apne low-income workers ko sponsor kar sakti hain — "
            "applications **10 Oct 2026** tak, first-come-first-served, sirf hajj.mora.gov.pk par. "
            "Employer apply karega aur employer hi pay karega.")
    st.markdown("🔗 [Ministry of Religious Affairs](https://mora.gov.pk) · "
                "🔗 [Hajj portal](https://hajj.mora.gov.pk)")
    st.divider()
    st.markdown("<div class='sec-title' style='font-size:24px'>Umrah</div>", unsafe_allow_html=True)
    st.write("Umrah private operators ke through hota hai. **Advance payment se pehle** operator Ministry "
             "ke approved list me check karo (mora.gov.pk). Bina license wale agent ko paise mat do.")
    st.caption("News sources: PakEra, Abb Takk, UrduPoint, 24 News HD (1–3 Oct 2026)")

# ================= TAB 4: DIRECTORY =================
with tab_dir:
    st.markdown("<div class='sec-title'>📚 Service Directory</div>"
                "<div class='sec-sub'>24 sarkari services, 10 categories — har ek ke sath official link.</div>",
                unsafe_allow_html=True)
    cats = {}
    for s in KB:
        cats.setdefault(s.get("cat", "Other"), []).append(s)
    for cat in sorted(cats):
        with st.expander(f"{cat} — {len(cats[cat])} services", expanded=False):
            cards = ""
            for s in cats[cat]:
                links = " &nbsp;·&nbsp; ".join(
                    f"<a href=\"{l['url']}\" target=\"_blank\">🔗 {l['label']}</a>" for l in s["links"]
                )
                cards += (f"<div class='svc-card'><span class='cat'>{cat}</span>"
                          f"<h4>{s['title']}</h4><p>{s['summary']}</p><div>{links}</div></div>")
            st.markdown(cards, unsafe_allow_html=True)

# ================= TAB 5: MAUSAM =================
with tab_weather:
    st.markdown("<div class='sec-title'>🌤️ Mausam</div>"
                "<div class='sec-sub'>Pakistan ke baray shehron ka taza mausam — Open-Meteo (bina key ke, free).</div>",
                unsafe_allow_html=True)
    city = st.selectbox("Sheher chuno", list(PK_CITIES.keys()))
    lat, lon = PK_CITIES[city]

    @st.cache_data(ttl=600)
    def _wx(lat, lon):
        return fetch_weather(lat, lon)

    try:
        w = _wx(lat, lon)
        st.markdown(f"""<div class="stat-band">
          <div class="stat-chip"><div class="num">{w['emoji']} {w['temp']}°C</div><div class="lbl">{city.upper()} — {w['desc'].upper()}</div></div>
          <div class="stat-chip"><div class="num">{w['feels']}°C</div><div class="lbl">MEHSOOS HOTA HAI</div></div>
          <div class="stat-chip"><div class="num">{w['humidity']}%</div><div class="lbl">HUMIDITY</div></div>
          <div class="stat-chip"><div class="num">{w['wind']} km/h</div><div class="lbl">HAWA</div></div>
        </div>""", unsafe_allow_html=True)
        st.markdown("<div class='sec-title' style='font-size:22px'>7 din ki forecast</div>", unsafe_allow_html=True)
        st.dataframe(
            [{"Din": d["date"], "Mausam": f"{d['emoji']} {d['desc']}",
              "Max (°C)": d["max"], "Min (°C)": d["min"]} for d in w["days"]],
            use_container_width=True, hide_index=True,
        )
    except Exception as e:
        st.warning(f"Mausam ka data is waqt nahi mil saka ({e}). Thori der baad try karo.")

# ================= TAB 6: TAZA KHABRAIN =================
with tab_news:
    st.markdown("<div class='sec-title'>📰 Taza Khabrain</div>"
                "<div class='sec-sub'>Dawn, Geo News aur Express Tribune ki taza headlines — seedha unki websites se.</div>",
                unsafe_allow_html=True)

    @st.cache_data(ttl=900)
    def _news():
        return fetch_news()

    try:
        items = _news()
        if not items:
            st.warning("Khabrain is waqt nahi mil sakin. Thori der baad refresh karo.")
        for it in items:
            st.markdown(
                f"<div class='svc-card'><span class='cat'>{it['source']}</span>"
                f"<h4>{it['title']}</h4>"
                f"<p style='color:#6B6455;font-size:12.5px'>{it['date']}</p>"
                f"<div><a href=\"{it['link']}\" target=\"_blank\">🔗 Poori khabar parho</a></div></div>",
                unsafe_allow_html=True,
            )
    except Exception as e:
        st.warning(f"Khabrain is waqt nahi mil sakin ({e}).")

# ================= TAB 7: CURRENCY =================
with tab_fx:
    st.markdown("<div class='sec-title'>💱 Currency Converter</div>"
                "<div class='sec-sub'>Taza exchange rates — USD, EUR, GBP, SAR, AED, PKR. Bina key ke, free.</div>",
                unsafe_allow_html=True)

    @st.cache_data(ttl=3600)
    def _fx():
        return fetch_rates()

    try:
        fx = _fx()
        rates = fx["rates"]
        st.caption(f"Rates date: {fx['date']} (1 USD = Rs {rates['PKR']:.2f})")
        c1, c2, c3 = st.columns(3)
        with c1:
            amt = st.number_input("Raqam", min_value=0.0, value=100.0, step=10.0)
        with c2:
            frm = st.selectbox("From", FX_CURRENCIES, index=0)
        with c3:
            to = st.selectbox("To", FX_CURRENCIES, index=5)
        result = convert(amt, frm, to, rates)
        st.markdown(f"""<div class="stat-band"><div class="stat-chip">
          <div class="num">{result:,.2f} {to}</div>
          <div class="lbl">{amt:,.2f} {FX_NAMES[frm]} =</div></div></div>""",
                    unsafe_allow_html=True)
        st.markdown("<div class='sec-title' style='font-size:22px'>Aaj ke rates (1 unit = kitne PKR)</div>",
                    unsafe_allow_html=True)
        st.dataframe(
            [{"Currency": f"{c} — {FX_NAMES[c]}",
              "1 unit = PKR": round(rates[c] and rates["PKR"] / rates[c], 2)}
             for c in ["USD", "EUR", "GBP", "SAR", "AED"]],
            use_container_width=True, hide_index=True,
        )
    except Exception as e:
        st.warning(f"Rates is waqt nahi mil sakay ({e}). Thori der baad try karo.")

# ================= TAB 8: AI TOOLS =================
with tab_ai:
    st.markdown("<div class='sec-title'>🤖 AI Tools</div>"
                "<div class='sec-sub'>Muft AI tools — apna data upload karo, AI se sawal pocho. 100% free.</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='sec-title' style='font-size:22px'>📊 CSV Data Analyst</div>", unsafe_allow_html=True)
    st.write("Apni CSV file upload karo (masalan kharcha, sales, ya fees ka record) — "
             "pehle summary dekho, phir AI se sawal pocho.")

    csv_file = st.file_uploader("CSV file upload karo", type=["csv"], key="csv_up")
    if csv_file:
        try:
            text = csv_file.getvalue().decode("utf-8-sig")
            info = analyze_csv(text)
            st.success(f"File parh li: **{info['n_rows']} rows**, **{len(info['headers'])} columns**")
            with st.expander("🔍 Pehli 5 rows dekho"):
                st.dataframe(info["head"], use_container_width=True)
            with st.expander("📈 Column stats"):
                if info["stats"]:
                    st.dataframe(
                        [{"Column": h, "Count": s["count"], "Min": s["min"],
                          "Max": s["max"], "Average": s["avg"]}
                         for h, s in info["stats"].items()],
                        use_container_width=True, hide_index=True,
                    )
                else:
                    st.write("Koi numeric column nahi mila — sirf text data hai.")

            if "csv_qa" not in st.session_state:
                st.session_state.csv_qa = []
            for m in st.session_state.csv_qa:
                with st.chat_message("user" if m["role"] == "user" else "assistant"):
                    st.markdown(m["content"])
            q = st.chat_input("Data ke baray me sawal pocho... masalan 'sab se zyada kharcha kis me hua?'")
            if q:
                st.session_state.csv_qa.append({"role": "user", "content": q})
                with st.chat_message("user"):
                    st.markdown(q)
                with st.chat_message("assistant"):
                    with st.spinner("Soch raha hoon..."):
                        try:
                            msgs = [
                                {"role": "system",
                                 "content": "You are a data analyst. Answer ONLY from the DATA SUMMARY below. "
                                            "Never invent numbers not in the summary. Language: Roman Urdu, short. "
                                            "DATA SUMMARY:\n" + info["context"]},
                                {"role": "user", "content": q},
                            ]
                            answer, provider = llm_chat(msgs, lambda s: st.secrets.get(s, ""))
                            answer += f"\n\n*via {provider}*"
                        except Exception as e:
                            answer = f"Maazrat, jawab nahi de saka ({e})."
                    st.markdown(answer)
                st.session_state.csv_qa.append({"role": "assistant", "content": answer})
                st.rerun()
        except Exception as e:
            st.error(f"CSV nahi parh saka: {e}")
    else:
        st.info("👆 Pehle CSV upload karo — phir summary aur AI sawal-jawab yahin hoga.")

st.divider()
st.caption("Concept: America.gov (US, Sep 2026) se inspired · Unofficial demo · Flights: OpenSky Network")
