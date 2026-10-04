# Pakistan Sahulat AI (Concept Demo)

America.gov (US, Sep 2026) se inspired — Pakistan ki sarkari services ke liye AI assistant ka **unofficial concept demo**. Sawal likho ya bolo (Urdu/English), knowledge base se jawab + official links.

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
`kb.json` me 14 services: NADRA (CNIC/NICOP/FRC), Passport (DGIP), BISP 8171, Vote 8300 (ECP), Driving License (Punjab/Sindh), FBR filer, Birth certificate, Domicile, FIR, KE bill. Assistant sirf isi KB se jawab deta hai + official link lazmi deta hai. Fees/rules change hote rehte hain — app har jawab me official link par confirm karne ko kehta hai.

## Note
Yeh hukumat-e-Pakistan ki official website **nahi** — concept demo hai. Koi transaction/apply feature nahi, sirf maloomat + routing (bilkul America.gov ke launch jaisa).
