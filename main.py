import os
import re
import time
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ===== SECRETS FROM GITHUB =====
YOUR_GMAIL = os.getenv("YOUR_GMAIL") # hydhirehubofficial@gmail.com
APP_PASSWORD = os.getenv("APP_PASSWORD")
BLOGGER_EMAIL = os.getenv("BLOGGER_EMAIL") # xxxxx@blogger.com
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT_ID")
BLOG_URL = "https://hydhirehub.blogspot.com"

POSTED_FILE = "jobs_posted.txt"

# ===== 1. DUPLICATE CONTROL =====
def load_posted():
    if not os.path.exists(POSTED_FILE):
        open(POSTED_FILE, 'w').close()
        return set()
    with open(POSTED_FILE, 'r', encoding='utf-8') as f:
        return set([l.strip().lower() for l in f if l.strip()])

def save_posted(title):
    clean = re.sub(r'\|\s*\d+\s*$', '', title).strip().lower()
    with open(POSTED_FILE, 'a', encoding='utf-8') as f:
        f.write(clean + "\n")

posted_set = load_posted()
current_set = set()

def is_duplicate(title):
    # Autodesk | Cloud Sales Specialist | Pan India (WFH) | 10647 -> Autodesk | Cloud Sales Specialist
    t = re.sub(r'\|\s*\d+\s*$', '', title) # last number remove
    parts = t.split('|')
    if len(parts) >= 2:
        key = (parts[0].strip() + "|" + parts[1].strip()).lower()
    else:
        key = t.lower()

    if key in posted_set or key in current_set:
        return True
    current_set.add(key)
    return False

# ===== 2. FULL TIME ONLY FILTER =====
def is_valid_job(title):
    low = title.lower()
    # Internship unte OUT
    if "internship" in low or "intern " in low:
        print(f"❌ SKIP Internship: {title}")
        return False
    return True

# ===== 3. BLOGGER POST LINK FINDER =====
def get_real_link(title):
    time.sleep(8) # Blogger indexing time
    try:
        feed = f"{BLOG_URL}/feeds/posts/default?alt=json&max-results=10"
        data = requests.get(feed, timeout=15).json()
        search_word = title.split('|')[0].strip().lower()
        for entry in data['feed'].get('entry', []):
            if search_word in entry['title']['$t'].lower():
                for link in entry['link']:
                    if link['rel'] == 'alternate':
                        return link['href']
        return data['feed']['entry'][0]['link'][2]['href']
    except:
        return BLOG_URL

# ===== 4. POST TO BLOGGER VIA EMAIL =====
def post_to_blogger(job):
    title = job['title']

    if not is_valid_job(title):
        return None
    if is_duplicate(title):
        print(f"❌ SKIP Duplicate: {title}")
        return None

    html_body = f"""
    <h2>{title}</h2>
    <p>{job['desc']}</p>
    <p><b>Location:</b> {job['location']}</p>
    <p><b>Apply:</b> <a href="{job['apply_url']}">{job['apply_url']}</a></p>
    <p><br>Source: HYD Hire Hub | {datetime.now().strftime('%d %b %Y')}</p>
    """

    msg = MIMEMultipart()
    msg['From'] = YOUR_GMAIL
    msg['To'] = BLOGGER_EMAIL
    msg['Subject'] = title
    msg.attach(MIMEText(html_body, 'html'))

    with smtplib.SMTP('smtp.gmail.com', 587) as s:
        s.starttls()
        s.login(YOUR_GMAIL, APP_PASSWORD)
        s.send_message(msg)

    print(f"✅ POSTED: {title}")
    save_posted(title)
    link = get_real_link(title)
    print(f"🔗 BLOG URL FOUND: {link}")
    return link

def send_telegram(title, link):
    if not TELEGRAM_TOKEN: return
    text = f"🚀 <b>{title}</b>\n\n🔗 {link}\n\n#FullTime #HYDJobs"
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                  data={"chat_id": TELEGRAM_CHAT, "text": text, "parse_mode": "HTML"})

# ===== 5. MAIN - NEE JOB FETCH LOGIC =====
def main():
    # Nee existing jobs fetching code ikkada undali
    # Example jobs list - Nee code lo replace chey
    jobs = [] # fetch_jobs_from_source() -> list of dicts

    # FOR TEST: jobs = [{"title":"Autodesk | Cloud Sales | Pan India","desc":"Full time role","location":"Pan India","apply_url":"https://..."}]

    for job in jobs:
        link = post_to_blogger(job)
        if link:
            send_telegram(job['title'], link)
            time.sleep(5)

if __name__ == "__main__":
    main()
