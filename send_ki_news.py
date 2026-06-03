import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from html import escape

RESEND_API_KEY = os.environ["RESEND_API_KEY"]
TO_EMAIL = "thomasschreitel@gmail.com"
FROM_EMAIL = "KI News <newsletter@web-profi24.de>"

RSS_FEEDS = [
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/technology-lab"),
    ("Hacker News AI", "https://hnrss.org/newest?q=AI+LLM+GPT&points=50"),
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; KI-Newsletter/1.0)"}


def fetch_feed(name, url, max_items=3):
    try:
        r = requests.get(url, timeout=12, headers=HEADERS)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        items = []
        for item in root.findall(".//item")[:max_items]:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            desc_raw = item.findtext("description", "").strip()
            # Strip HTML tags from description
            import re
            desc = re.sub(r"<[^>]+>", "", desc_raw)[:300].strip()
            if title and link:
                items.append({"title": title, "link": link, "desc": desc, "source": name})
        return items
    except Exception as e:
        print(f"Feed {name} fehlgeschlagen: {e}")
        return []


def build_html(news_items, date_str):
    items_html = ""
    for i, item in enumerate(news_items, 1):
        items_html += f"""
        <tr>
          <td style="padding:20px 0; border-bottom:1px solid #f0f0f0;">
            <p style="margin:0 0 4px 0; font-size:12px; color:#888; font-family:sans-serif;">{escape(item['source'])}</p>
            <h3 style="margin:0 0 8px 0; font-size:16px; font-family:sans-serif;">
              <a href="{escape(item['link'])}" style="color:#1a1a1a; text-decoration:none;">{escape(item['title'])}</a>
            </h3>
            <p style="margin:0; font-size:14px; line-height:1.6; color:#444; font-family:sans-serif;">{escape(item['desc'])}</p>
            <a href="{escape(item['link'])}" style="display:inline-block; margin-top:8px; font-size:13px; color:#0066cc; font-family:sans-serif;">Weiterlesen →</a>
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0; padding:0; background:#f5f5f5;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5; padding:30px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:8px; overflow:hidden; max-width:600px; width:100%;">

        <!-- Header -->
        <tr><td style="background:#1a1a1a; padding:28px 32px;">
          <h1 style="margin:0; color:#ffffff; font-size:22px; font-family:sans-serif;">
            KI-News <span style="color:#888; font-size:16px; font-weight:normal;">– {date_str}</span>
          </h1>
          <p style="margin:6px 0 0 0; color:#aaa; font-size:13px; font-family:sans-serif;">Täglich zusammengestellt für Thomas Schreitel</p>
        </td></tr>

        <!-- News -->
        <tr><td style="padding:8px 32px 24px 32px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            {items_html}
          </table>
        </td></tr>

        <!-- Footer -->
        <tr><td style="background:#f9f9f9; padding:20px 32px; border-top:1px solid #eee;">
          <p style="margin:0; font-size:12px; color:#aaa; font-family:sans-serif;">
            Automatisch generiert · web-profi24.de
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send_email(subject, html):
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": FROM_EMAIL,
            "to": [TO_EMAIL],
            "subject": subject,
            "html": html,
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    print("Feeds werden geladen...")
    all_items = []
    for name, url in RSS_FEEDS:
        items = fetch_feed(name, url)
        all_items.extend(items)
        print(f"  {name}: {len(items)} Artikel")

    # Deduplizieren nach Titel
    seen = set()
    unique_items = []
    for item in all_items:
        key = item["title"].lower()[:60]
        if key not in seen:
            seen.add(key)
            unique_items.append(item)

    top_items = unique_items[:8]
    date_str = datetime.now().strftime("%d.%m.%Y")

    print(f"\n{len(top_items)} Meldungen ausgewählt. E-Mail wird erstellt...")
    html = build_html(top_items, date_str)

    print("E-Mail wird versendet...")
    result = send_email(f"KI-News – {date_str}", html)
    print(f"Erfolg! ID: {result.get('id')}")
