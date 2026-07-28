import requests, json, os, smtplib, random
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
import time
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
YOUR_GMAIL = os.environ.get("YOUR_GMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
BLOGGER_EMAIL = os.environ.get("BLOGGER_EMAIL")

def get_internshala():
    jobs = []
    try:
        url = "https://internshala.com/jobs/jobs-in-hyderabad/"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, 'lxml')
        for card in soup.select('.individual_internship_details')[:3]:
            try:
                title = card.select_one('.job-internship-name').text.strip()
                company = card.select_one('.company-name').text.strip()
                link = "https://internshala.com" + card.select_one('a.job-title-href')['href']
                jobs.append({"title": title, "company": company, "link": link, "source": "Internshala"})
            except: continue
    except: pass
    return jobs

def get_indeed():
    jobs = []
    try:
        url = "https://rss.indeed.com/rss?q=fresher&l=Hyderabad"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, 'lxml')
        for item in soup.find_all('item')[:4]:
            try:
                title = item.title.text.strip()
                link = item.link.text.strip()
                # Title nundi company teeyadam
                company = title.split('-')[-1].strip() if '-' in title else "Top MNC"
                role = title.split('-')[0].strip()
                jobs.append({"title": role, "company": company, "link": link, "source": "Indeed"})
            except: continue
    except: pass
    return jobs

def is_posted(link):
    try:
        with open('posted.json','r') as f: return link in json.load(f)
    except: return False

def save_link(link):
    data = []
    if os.path.exists('posted.json'):
        try:
            with open('posted.json','r') as f: data = json.load(f)
        except: pass
    data.append(link)
    data = data[-100:]
    with open('posted.json','w') as f: json.dump(data,f)

def post_telegram(job):
    # NUVVU ADIGINA OLD STYLE FORMAT LO
    text = f"""🔥 {job['company']} Off Campus Drive 2026

💼 Job Role: {job['title']}
🏢 Company: {job['company']}
🎓 Qualification: B.E/B.Tech/B.Sc/BCA/Any Graduate
🔹 Batch: 2023/2024/2025/2026
🆕 Experience: Freshers
📍 Location: Hyderabad
🌐 Source: {job['source']}

🌐 Apply Here:
{job['link']}

━━━━━━━━━━━━━━━━━━━━
📢 Join Our Telegram Channel
https://t.me/HydHireHub

🌐 Visit Our Blog
https://hydhirehub.blogspot.com
━━━━━━━━━━━━━━━━━━━━
✅ Follow us for Daily Updates
• Off Campus Drives • Freshers Jobs • Experienced Jobs
"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": text, "disable_web_page_preview": True})

def post_blogger(job):
    # Blogger lo kuda same rich format
    html = f"""
    <h2>{job['company']} Off Campus Drive 2026 - {job['title']}</h2>
    <p>🔥 <b>{job['company']} Off Campus Drive 2026</b></p>
    <p>💼 Job Role: {job['title']}<br>
    🏢 Company: {job['company']}<br>
    🎓 Qualification: B.E/B.Tech/B.Sc/BCA<br>
    🔹 Batch: 2023/2024/2025<br>
    🆕 Experience: Freshers<br>
    📍 Location: Hyderabad</p>
    <p><b>Apply Here:</b> <a href="{job['link']}">{job['link']}</a></p>
    <p>━━━━━━━━━━━━<br>
    Join Telegram: https://t.me/HydHireHub<br>
    Blog: https://hydhirehub.blogspot.com</p>
    """
    msg = MIMEText(html, "html")
    msg['Subject'] = f"{job['company']} Off Campus Drive 2026 - {job['title']} - Hyderabad"
    msg['From'] = YOUR_GMAIL
    msg['To'] = BLOGGER_EMAIL
    with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
        s.login(YOUR_GMAIL, APP_PASSWORD)
        s.send_message(msg)

all_jobs = []
all_jobs.extend(get_internshala())
all_jobs.extend(get_indeed())
random.shuffle(all_jobs)

count=0
for job in all_jobs:
    if not is_posted(job['link']) and job['link'].startswith('http'):
        if count>=2: break
        print(f"Posting {job['title']}")
        post_telegram(job)
        post_blogger(job)
        save_link(job['link'])
        count+=1
        time.sleep(5)
