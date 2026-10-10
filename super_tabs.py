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


def fetch_weather(lat: float, lon: float, timeout: int = 12) -> dict:
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


def fetch_news(limit_per_feed: int = 8, timeout: int = 12) -> list:
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


def fetch_rates(timeout: int = 12) -> dict:
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


# ---------------- Prayer Times (Aladhan, keyless) ----------------
# https://aladhan.com/prayer-times-api — free, no signup, worldwide.
# NOTE: api.aladhan.com issues a 302 redirect; requests follows it by default.
METHODS = {
    "Karachi (Univ. of Islamic Sciences)": 1,
    "Muslim World League": 3,
    "Egyptian General Authority": 5,
    "Umm al-Qura (Makkah)": 4,
    "Dubai / UAE": 16,
    "Kuwait": 9,
    "Qatar": 10,
    "Iran (Ja'fari)": 7,
}

PRAYER_UR = {
    "Fajr": ("🌅", "Fajr"), "Sunrise": ("☀️", "Tulu-e-Aftab"),
    "Dhuhr": ("🌞", "Zuhr"), "Asr": ("🌤️", "Asr"),
    "Maghrib": ("🌇", "Maghrib"), "Isha": ("🌙", "Isha"),
}


def reverse_geocode(lat: float, lon: float, timeout: int = 12) -> str:
    """City, Country from GPS coordinates (BigDataCloud, free, no key)."""
    import requests
    try:
        r = requests.get(
            "https://api.bigdatacloud.net/data/reverse-geocode-client",
            params={"latitude": lat, "longitude": lon, "localityLanguage": "en"},
            headers=UA, timeout=timeout,
        )
        r.raise_for_status()
        d = r.json()
        city = d.get("city") or d.get("locality") or ""
        country = d.get("countryName") or ""
        label = ", ".join(x for x in (city, country) if x)
        return label or f"{lat:.3f}, {lon:.3f}"
    except Exception:
        return f"{lat:.3f}, {lon:.3f}"


def fetch_prayer_times_by_coords(lat: float, lon: float, method: int = 1, school: int = 1,
                                 timeout: int = 12) -> dict:
    """Prayer times by GPS coordinates via Aladhan. school=1 -> Hanafi Asr.
    Raises on failure."""
    import requests
    from datetime import date
    today = date.today().strftime("%d-%m-%Y")
    r = requests.get(
        f"https://api.aladhan.com/v1/timings/{today}",
        params={"latitude": lat, "longitude": lon, "method": method, "school": school},
        headers=UA, timeout=timeout,
    )
    r.raise_for_status()
    data = r.json()["data"]
    timings = {k: v[:5] for k, v in data["timings"].items()
               if k in PRAYER_UR}
    hijri = data["date"]["hijri"]
    return {
        "timings": timings,
        "date": data["date"]["readable"],
        "hijri": f"{hijri['day']} {hijri['month']['en']} {hijri['year']}H",
        "source": "Aladhan API (free)",
    }
def fetch_prayer_times(city: str, country: str, method: int = 1, school: int = 1,
                       timeout: int = 12) -> dict:
    """Prayer times for any city worldwide via Aladhan. school=1 -> Hanafi Asr.
    Raises on failure."""
    import requests
    r = requests.get(
        "https://api.aladhan.com/v1/timingsByCity",
        params={"city": city, "country": country, "method": method, "school": school},
        headers=UA, timeout=timeout,
    )
    r.raise_for_status()
    data = r.json()["data"]
    timings = {k: v[:5] for k, v in data["timings"].items()
               if k in PRAYER_UR}
    hijri = data["date"]["hijri"]
    out = {
        "timings": timings,
        "date": data["date"]["readable"],
        "hijri": f"{hijri['day']} {hijri['month']['en']} {hijri['year']}H",
    }
    out["source"] = "Aladhan API (free)"
    return out


DI_CITY_SLUGS = {
    "Karachi": "karachi", "Lahore": "lahore", "Islamabad": "islamabad",
    "Rawalpindi": "rawalpindi", "Peshawar": "peshawar", "Quetta": "quetta",
    "Multan": "multan", "Faisalabad": "faisalabad", "Sialkot": "sialkot",
    "Gujranwala": "gujranwala", "Bahawalpur": "bahawalpur", "Hyderabad": "hyderabad",
}


def _di_hhmm(s: str) -> str:
    """'05:10:51 AM' -> '05:10' (24h)."""
    import re
    m = re.match(r"(\d+):(\d+)(?::\d+)?\s*(AM|PM)", s.strip(), re.I)
    if not m:
        raise ValueError(f"bad time: {s}")
    h, mi, ap = int(m.group(1)), m.group(2), m.group(3).upper()
    if ap == "PM" and h != 12:
        h += 12
    if ap == "AM" and h == 12:
        h = 0
    return f"{h:02d}:{mi}"


def fetch_dawateislami(city: str, timeout: int = 12) -> dict:
    """Dawat-e-Islami prayer times (Hanafi) for Pakistani cities, scraped from
    dawateislami.net monthly timetable. Same dict shape as fetch_prayer_times.
    Raises on failure (caller falls back to Aladhan)."""
    import re
    import requests
    from datetime import date
    slug = DI_CITY_SLUGS.get(city.strip().title())
    if not slug:
        slug = re.sub(r"[^a-z-]", "", city.strip().lower().replace(" ", "-"))
    r = requests.get(
        f"https://www.dawateislami.net/prayer-times/world/pakistan/{slug}-prayer-times",
        headers=UA, timeout=timeout,
    )
    r.raise_for_status()
    tables = re.findall(r'<table class="table-striped table-bordered">(.*?)</table>',
                        r.text, re.S)
    cal = next((t for t in tables if "Dahwa-e-Kubra" in t and "Asr(Hanafi)" in t), None)
    if not cal:
        raise ValueError("Dawat-e-Islami timetable nahi mila")
    today = str(date.today().day)
    for row in re.findall(r"<tr>(.*?)</tr>", cal, re.S):
        cells = [re.sub(r"<[^>]+>", "", c).strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        # day, Fajr, Sunrise, Dahwa, Zuhr, AsrShafi, AsrHanafi, Maghrib, IshaShafi, IshaHanafi
        if len(cells) >= 10 and cells[0] == today:
            hijri = ""
            try:
                hr = requests.get("https://api.aladhan.com/v1/gToH",
                                  params={"date": date.today().strftime("%d-%m-%Y")},
                                  headers=UA, timeout=timeout)
                hd = hr.json()["data"]["hijri"]
                hijri = f"{hd['day']} {hd['month']['en']} {hd['year']}H"
            except Exception:
                pass
            return {
                "timings": {
                    "Fajr": _di_hhmm(cells[1]), "Sunrise": _di_hhmm(cells[2]),
                    "Dhuhr": _di_hhmm(cells[4]), "Asr": _di_hhmm(cells[6]),
                    "Maghrib": _di_hhmm(cells[7]), "Isha": _di_hhmm(cells[9]),
                },
                "date": date.today().strftime("%d %b %Y"),
                "hijri": hijri,
                "source": "Dawat-e-Islami",
            }
    raise ValueError("aaj ki tareekh timetable me nahi mili")
