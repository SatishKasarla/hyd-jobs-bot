import requests, json, os, smtplib, random, time
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
YOUR_GMAIL = os.environ.get("YOUR_GMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
BLOGGER_EMAIL = os.environ.get("BLOGGER_EMAIL")

print(f"Bot Token Exists: {bool(BOT_TOKEN)}")
print(f"Channel ID: {CHANNEL_ID}")
print(f"Gmail Exists: {bool(YOUR_GMAIL)}")

def get_jobs():
    jobs=[]
    # METHOD 1: Indeed RSS - Always Works
    try:
        print("Trying Indeed RSS...")
        r = requests.get("https://rss.indeed.com/rss?q=Software+Developer&l=Hyderabad", headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, 'xml')
        items = soup.find_all('item')
        print(f"Indeed Found: {len(items)}")
        for item in items[:2]:
            title = item.title.text.strip()
            link = item.link.text.strip()
            jobs.append({"title": title[:50], "company": "Top MNC", "link": link, "source": "Indeed"})
    except Exception as e:
        print(f"Indeed Error: {e}")

    # METHOD 2: Fallback - If Indeed fails, use ready jobs
    if not jobs:
        print("Using Fallback Jobs - Indeed Blocked")
        jobs = [
            {"title": "Software Engineer", "company": "TCS", "link": "https://www.tcs.com/careers", "source": "TCS Careers"},
            {"title": "Python Developer", "company": "Infosys", "link": "https://www.infosys.com/careers", "source": "Infosys Careers"},
        ]
    return jobs

def is_posted(link):
    try:
        with open('posted.json','r') as f: 
            data=json.load(f)
            return link in data
    except: return False

def save_link(link):
    data=[]
    if os.path.exists('posted.json'):
        try:
            with open('posted.json','r') as f: data=json.load(f)
        except: pass
    data.append(link)
    with open('posted.json','w') as f: json.dump(data[-50:], f)

def post_telegram(job):
    text = f"""🔥 {job['company']} Off Campus Drive 2026

💼 Job Role: {job['title']}
🏢 Company: {job['company']}
🎓 Qualification: B.E/B.Tech/B.Sc/BCA
🔹 Batch: 2023/2024/2025
🆕 Experience: Freshers
📍 Location: Hyderabad
🔗 Source: {job['source']}

🌐 Apply Here:
{job['link']}

━━━━━━━━━━━━━━━━━━━━
📢 Join Our Telegram Channel
https://t.me/HydHireHub
🌐 Visit Our Blog
https://hydhirehub.blogspot.com
"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        resp = requests.post(url, data={"chat_id": CHANNEL_ID, "text": text, "disable_web_page_preview": True}, timeout=15)
        print(f"Telegram Response: {resp.status_code} - {resp.text[:200]}")
    except Exception as e:
        print(f"Telegram Error: {e}")

def post_blogger(job):
    try:
        html = f"""<h2>{job['company']} - {job['title']} - Hyderabad</h2>
        <p>💼 Role: {job['title']}<br>🏢 Company: {job['company']}<br>🎓 Qualification: Any Graduate<br>📍 Location: Hyderabad</p>
        <p>Apply: <a href="{job['link']}">{job['link']}</a></p>
        <p>Join: https://t.me/HydHireHub | Blog: https://hydhirehub.blogspot.com</p>"""
        msg = MIMEText(html, "html")
        msg['Subject'] = f"{job['company']} Hiring {job['title']} 2026"
        msg['From'] = YOUR_GMAIL
        msg['To'] = BLOGGER_EMAIL
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
            s.login(YOUR_GMAIL, APP_PASSWORD)
            s.send_message(msg)
        print(f"Blogger Sent OK: {job['title']}")
    except Exception as e:
        print(f"Blogger Error: {e}")

jobs = get_jobs()
print(f"Total Jobs to Post: {len(jobs)}")
count=0
for job in jobs:
    if not is_posted(job['link']):
        if count>=2: break
        post_telegram(job)
        post_blogger(job)
        save_link(job['link'])
        count+=1
        time.sleep(3)

if count==0:
    print("No new jobs - All already posted. Delete posted.json to repost.")
