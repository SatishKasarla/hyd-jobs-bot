import requests, json, os, smtplib, random, time
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
YOUR_GMAIL = os.environ.get("YOUR_GMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
BLOGGER_EMAIL = os.environ.get("BLOGGER_EMAIL")
BLOG_URL = "https://hydhirehub.blogspot.com"

def is_english_only(text):
    # German/French/Dutch filter
    bad_words = ["Du hast", "Aufgaben", "Mitarbeit", "für", "und", "der", "die", "das", "Erfahrung", "Bist du", "Unternehmen", "München", "Berlin"]
    t = text.lower()
    # If more than 1 bad word, skip
    count = sum(1 for w in bad_words if w.lower() in t)
    if count >= 2:
        return False
    # Must have English letters mostly
    return True

def get_only_hyd_jobs():
    jobs=[]
    headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # Source 1: Indeed Hyderabad - Software
    try:
        url="https://rss.indeed.com/rss?q=software&l=Hyderabad&sort=date"
        r=requests.get(url, headers=headers, timeout=15)
        soup=BeautifulSoup(r.text, 'xml')
        for item in soup.find_all('item')[:6]:
            title=item.title.text.split('-')[0].strip()
            desc=BeautifulSoup(item.description.text, 'html.parser').get_text()
            if is_english_only(title) and is_english_only(desc):
                jobs.append({
                    "title": title[:80],
                    "company": title.split('at')[-1].strip() if 'at' in title.lower() else "Top MNC Hyderabad",
                    "link": item.link.text,
                    "desc": desc[:800],
                    "location": "Hyderabad"
                })
    except Exception as e:
        print(f"Indeed1 Error {e}")

    # Source 2: Indeed Hyderabad - Fresher
    try:
        url="https://rss.indeed.com/rss?q=fresher+developer&l=Hyderabad&sort=date"
        r=requests.get(url, headers=headers, timeout=15)
        soup=BeautifulSoup(r.text, 'xml')
        for item in soup.find_all('item')[:6]:
            title=item.title.text.split('-')[0].strip()
            desc=BeautifulSoup(item.description.text, 'html.parser').get_text()
            if is_english_only(title) and is_english_only(desc):
                jobs.append({
                    "title": title[:80],
                    "company": "MNC Hiring Hyderabad",
                    "link": item.link.text,
                    "desc": desc[:800],
                    "location": "Hyderabad"
                })
    except: pass

    # Source 3: Backup - ArbeitNow English Remote only if Indeed fails
    if len(jobs) < 2:
        try:
            r=requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=15).json()
            for j in r['data'][:10]:
                if is_english_only(j['title']) and is_english_only(j['description']):
                    jobs.append({
                        "title": j['title'],
                        "company": j['company_name'],
                        "link": j['url'],
                        "desc": j['description'][:800],
                        "location": "Hyderabad (Remote)"
                    })
        except: pass

    random.shuffle(jobs)
    print(f"FINAL HYD ENGLISH JOBS: {len(jobs)}")
    return jobs

def is_posted(link):
    try:
        with open('posted.json','r') as f:
            return link in json.load(f)
    except: return False

def save_link(link):
    data=[]
    if os.path.exists('posted.json'):
        try:
            with open('posted.json','r') as f: data=json.load(f)
        except: pass
    data.append(link)
    with open('posted.json','w') as f: json.dump(data[-400:], f)

def post_blogger(job):
    html=f"""
    <div style="font-family:Arial;line-height:1.8;">
    <h1>{job['company']} Hiring {job['title']} in Hyderabad 2026</h1>
    <p><b>HydHireHub Hyderabad Jobs:</b> {job['company']} is hiring {job['title']} for Hyderabad location. Great opportunity for 2023-2025 batch freshers.</p>
    <div style="background:#eef2ff;padding:15px;border-radius:8px;">
    <p>💼 Job Role: {job['title']}<br>🏢 Company: {job['company']}<br>🎓 Qualification: B.E/B.Tech/B.Sc/BCA/MCA/Any Graduate<br>🔹 Batch: 2023/2024/2025<br>🆕 Experience: Freshers & Experienced<br>📍 Location: Hyderabad<br>💰 Salary: As per Hyderabad Industry Standards</p>
    </div>
    <h3>Job Description - {job['location']}:</h3>
    <p>{job['desc']}</p>
    <p>This is a full-time job opportunity in Hyderabad. Work location is Hyderabad - HITEC City, Gachibowli, Madhapur, Kondapur. Candidates from Hyderabad or willing to relocate to Hyderabad can apply. This is a great chance to start career in Hyderabad IT industry.</p>
    <h3>Eligibility for Hyderabad Jobs:</h3>
    <p>Any Graduate, B.E, B.Tech, BCA, MCA, B.Sc can apply. Good communication skills and basic technical knowledge required. Freshers from 2023, 2024, 2025 batches eligible.</p>
    <div style="text-align:center;margin:30px 0;">
    <a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:16px 45px;text-decoration:none;border-radius:8px;font-weight:bold;font-size:18px;">🌐 Apply Here - Hyderabad</a>
    </div>
    <p>More Hyderabad Jobs: {BLOG_URL}</p>
    </div>
    """
    msg=MIMEText(html,"html")
    msg['Subject']=f"{job['company']} Off Campus Drive 2026 - {job['title']} - Hyderabad"
    msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
            s.login(YOUR_GMAIL, APP_PASSWORD); s.send_message(msg)
        print(f"Blogger OK: {job['title']}")
        return True
    except Exception as e:
        print(f"Blogger FAIL {e}"); return False

def get_latest_blog_url():
    time.sleep(80)
    try:
        r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=1", timeout=20)
        soup=BeautifulSoup(r.text,'xml')
        return soup.find('item').find('link').text
    except: return BLOG_URL

def post_telegram(job, blog_url):
    text=f"""🔥 {job['company']} Off Campus Drive 2026

💼 Job Role: {job['title']}
🏢 Company: {job['company']}
🎓 Qualification: B.E/B.Tech/B.Sc/BCA
🔹 Batch: 2023/2024/2025
🆕 Experience: Freshers
📍 Location: Hyderabad

🌐 Apply Here:
{blog_url}

━━━━━━━━━━━━━━━━━━━━
📢 Join Our Telegram Channel

https://t.me/HydHireHub

🌐 Visit Our Blog

https://hydhirehub.blogspot.com
"""
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHANNEL_ID, "text":text}, timeout=15)
        print("Telegram OK")
    except Exception as e:
        print(f"Telegram Error {e}")

jobs=get_only_hyd_jobs()
posted=False
for job in jobs:
    if not is_posted(job['link']):
        if post_blogger(job):
            b_url=get_latest_blog_url()
            post_telegram(job, b_url)
            save_link(job['link'])
            posted=True
            break

if not posted:
    print("No new job this cycle - all already posted")
