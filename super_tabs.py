"""Super-app helpers for Pakistan Sahulat AI (pure logic, no Streamlit).

All external APIs are keyless / no-signup:
- Weather: Open-Meteo (https://api.open-meteo.com)
- News: Dawn / Geo / Express Tribune RSS feeds (xml.etree, no new deps)
- Currency: exchangerate-api.com free v4 endpoint (no key)
- CSV analyst: pure-Python stats (no pandas)
"""
import csv
import io
import urllib.request
import xml.etree.ElementTree as ET

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

# ---------------- Weather ----------------
PK_CITIES = {
    "Karachi": (24.86, 67.01),
    "Lahore": (31.55, 74.34),
    "Islamabad": (33.68, 73.05),
    "Rawalpindi": (33.60, 73.04),
    "Peshawar": (34.02, 71.58),
    "Quetta": (30.18, 66.99),
    "Multan": (30.16, 71.52),
    "Faisalabad": (31.42, 73.08),
}

WMO = {
    0: ("☀️", "Saaf asman"), 1: ("🌤️", "Halke badal"), 2: ("⛅", "Juzvi badal"),
    3: ("☁️", "Abr-alood"), 45: ("🌫️", "Dhund"), 48: ("🌫️", "Barfili dhund"),
    51: ("🌦️", "Halki bonda-bandi"), 53: ("🌦️", "Bonda-bandi"), 55: ("🌧️", "Tez bonda-bandi"),
    61: ("🌧️", "Halki barish"), 63: ("🌧️", "Barish"), 65: ("⛈️", "Musaladhar barish"),
    71: ("🌨️", "Halki barf"), 73: ("🌨️", "Barf"), 75: ("❄️", "Tez barf"),
    80: ("🌧️", "Halki bochhar"), 81: ("🌧️", "Bochhar"), 82: ("⛈️", "Tez bochhar"),
    95: ("⛈️", "Garaj-chamak"), 96: ("⛈️", "Olon ke sath toofan"), 99: ("⛈️", "Shadeed toofan"),
}


def fetch_weather(lat: float, lon: float, timeout: int = 25) -> dict:
    """Current + 7-day forecast from Open-Meteo. Raises on failure."""
    url = ("https://api.open-meteo.com/v1/forecast?latitude=%.2f&longitude=%.2f"
           "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
           "wind_speed_10m,weather_code"
           "&daily=weather_code,temperature_2m_max,temperature_2m_min"
           "&timezone=Asia%%2FKarachi&forecast_days=7" % (lat, lon))
    import json
    req = urllib.request.Request(url, headers=UA)
    data = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    cur = data["current"]
    days = []
    for i in range(len(data["daily"]["time"])):
        code = data["daily"]["weather_code"][i]
        emoji, desc = WMO.get(code, ("🌡️", "Mausam"))
        days.append({
            "date": data["daily"]["time"][i][5:],  # MM-DD
            "emoji": emoji, "desc": desc,
            "max": round(data["daily"]["temperature_2m_max"][i]),
            "min": round(data["daily"]["temperature_2m_min"][i]),
        })
    emoji, desc = WMO.get(cur["weather_code"], ("🌡️", "Mausam"))
    return {
        "temp": round(cur["temperature_2m"], 1),
        "feels": round(cur["apparent_temperature"], 1),
        "humidity": cur["relative_humidity_2m"],
        "wind": round(cur["wind_speed_10m"], 1),
        "emoji": emoji, "desc": desc,
        "days": days,
    }


# ---------------- News ----------------
RSS_FEEDS = [
    ("Dawn", "https://www.dawn.com/feed"),
    ("Geo News", "https://www.geo.tv/rss/1/0"),
    ("Express Tribune", "https://tribune.com.pk/feed/home"),
]


def fetch_news(limit_per_feed: int = 8, timeout: int = 25) -> list:
    """Headlines from Pakistani news RSS feeds. Returns [{source,title,link,date}]."""
    out = []
    for source, url in RSS_FEEDS:
        try:
            req = urllib.request.Request(url, headers=UA)
            root = ET.fromstring(urllib.request.urlopen(req, timeout=timeout).read())
            channel = root.find("channel")
            if channel is None:
                continue
            for item in channel.findall("item")[:limit_per_feed]:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                pub = (item.findtext("pubDate") or "")[:16]
                if title and link:
                    out.append({"source": source, "title": title,
                                "link": link, "date": pub})
        except Exception:
            continue  # one dead feed must not kill the tab
    return out


# ---------------- Currency ----------------
FX_CURRENCIES = ["USD", "EUR", "GBP", "SAR", "AED", "PKR"]
FX_NAMES = {"USD": "US Dollar", "EUR": "Euro", "GBP": "British Pound",
            "SAR": "Saudi Riyal", "AED": "UAE Dirham", "PKR": "Pakistani Rupee"}


def fetch_rates(timeout: int = 25) -> dict:
    """USD-base rates from exchangerate-api.com free tier. Returns {rates, date}."""
    import json
    req = urllib.request.Request("https://api.exchangerate-api.com/v4/latest/USD",
                                 headers=UA)
    data = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    return {"rates": data["rates"], "date": data.get("date", "")}


def convert(amount: float, frm: str, to: str, rates: dict) -> float:
    """Convert via USD-base rates dict."""
    if frm == to:
        return amount
    usd = amount / rates[frm] if frm != "USD" else amount
    return usd * rates[to] if to != "USD" else usd


# ---------------- CSV analyst (no pandas) ----------------
def analyze_csv(text: str, max_rows: int = 2000) -> dict:
    """Pure-Python CSV summary. Returns {headers, n_rows, head, stats, context}."""
    reader = csv.reader(io.StringIO(text))
    rows = [r for i, r in enumerate(reader) if i < max_rows + 1]
    if not rows:
        raise ValueError("CSV khaali hai.")
    headers = [h.strip() for h in rows[0]]
    data = rows[1:]
    n_cols = len(headers)
    # numeric detection per column
    stats = {}
    for ci, h in enumerate(headers):
        vals = []
        for r in data:
            if ci < len(r):
                try:
                    vals.append(float(r[ci].replace(",", "").strip()))
                except (ValueError, AttributeError):
                    pass
        if len(vals) >= max(2, len(data) // 2) and data:
            vals.sort()
            stats[h] = {
                "count": len(vals), "min": round(vals[0], 2),
                "max": round(vals[-1], 2),
                "avg": round(sum(vals) / len(vals), 2),
            }
    head = [dict(zip(headers, r + [""] * (n_cols - len(r)))) for r in data[:5]]
    lines = [f"CSV: {len(data)} rows, {n_cols} columns.",
             "Columns: " + ", ".join(headers) + "."]
    for h, s in stats.items():
        lines.append(f"'{h}': {s['count']} numeric values, min {s['min']}, "
                     f"max {s['max']}, average {s['avg']}.")
    nonnum = [h for h in headers if h not in stats]
    if nonnum:
        lines.append("Text columns: " + ", ".join(nonnum) + ".")
    return {"headers": headers, "n_rows": len(data), "head": head,
            "stats": stats, "context": "\n".join(lines)}
