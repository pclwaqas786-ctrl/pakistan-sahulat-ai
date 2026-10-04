# Pakistan Sahulat AI (Concept Demo)

America.gov (US, Sep 2026) se inspired — Pakistan ki sarkari services ke liye AI assistant ka **unofficial concept demo**. Sawal likho ya bolo (Urdu/English), knowledge base se jawab + official links.

## Tabs (4)
- **💬 Assistant** — chat (Roman Urdu + English), voice input (Urdu, Groq Whisper), **PDF upload** (sarkari letter/form upload karke us par sawal pucho), suggested questions
- **✈️ Live Flights** — Pakistan + region ke upar live flights, real-time ADS-B data (OpenSky Network, free), Leaflet map + list, 60-sec refresh
- **🕋 Hajj & Umrah** — Hajj 2027 government scheme ki taza info (second instalment 5–20 Oct 2026, medical certificate lazmi, labour quota 10 Oct tak)
- **📚 Service Directory** — 24 services, 10 categories me browsable, official links ke sath

## Deploy (Streamlit Cloud, free)

1. Repo GitHub par push karo (neeche).
2. [share.streamlit.io](https://share.streamlit.io) → New app → repo select karo, main file `app.py`.
3. **App settings → Secrets** me ye add karo:
   ```toml
   GROQ_API_KEY = "gsk_...tumhari Groq key..."
   ```
   Key free me banti hai: console.groq.com/keys (sirf email, no credit card).
4. Deploy. Ho gaya.

## Local run
```bash
pip install -r requirements.txt
mkdir -p .streamlit
printf 'GROQ_API_KEY = "gsk_..."\n' > .streamlit/secrets.toml
streamlit run app.py
```

## Knowledge base
`kb.json` me 24 services, 10 categories: Identity, Travel, Welfare, Religious, Tax & Finance, Civic, Bills, Overseas, Property, Emergency. Assistant sirf isi KB se jawab deta hai + official link lazmi deta hai. Fees/rules change hote rehte hain — app har jawab me official link par confirm karne ko kehta hai.

## Note
Yeh hukumat-e-Pakistan ki official website **nahi** — concept demo hai. Koi transaction/apply feature nahi, sirf maloomat + routing (bilkul America.gov ke launch jaisa).
