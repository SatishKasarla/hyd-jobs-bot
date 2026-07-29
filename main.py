import requests, json, os, smtplib, random, time, re
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
YOUR_GMAIL = os.environ.get("YOUR_GMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
BLOGGER_EMAIL = os.environ.get("BLOGGER_EMAIL")
BLOG_URL = "https://hydhirehub.blogspot.com"

def parse_details(desc, title):
    text = (title + " " + desc).lower()
    if "mba" in text: qual = "B.E/B.Tech/MBA/MCA"
    elif "bca" in text or "bsc" in text: qual = "B.E/B.Tech/B.Sc/BCA/MCA"
    else: qual = "B.E/B.Tech/M.Tech/MCA"

    years = re.findall(r'20(?:2[3-6])', text)
    if years:
        uniq = sorted(list(set(years)))[:3]
        batch = "/".join(uniq)
    else:
        batch = "2024/2025/2026"

    if "0-1" in text or "fresher" in text: exp = "Freshers (0-1 Year)"
    elif "1-2" in text: exp = "0-2 Years"
    else: exp = "Freshers"

    if "remote" in text and "hyderabad" not in text: loc = "Remote (India)"
    elif "bangalore" in text and "hyderabad" not in text: loc = "Bangalore"
    else: loc = "Hyderabad"
    return qual, batch, exp, loc

def fetch_real_jobs():
    jobs=[]
    # ONLY Real API - No fake templates
    try:
        r=requests.get("https://jobicy.com/api/v2/remote-jobs?count=50&geo=india", timeout=20).json()
        for j in r.get('jobs',[]):
            title=j.get('jobTitle',''); desc=j.get('jobDescription',''); company=j.get('companyName','')
            # Strict real job filter
            if not title or not company: continue
            if any(x in title.lower() for x in ["für","unser","ä","ö","ü","ß"]): continue
            if "http" not in j.get('url',''): continue # Must have real apply link

            qual,batch,exp,loc = parse_details(desc, title)
            jobs.append({
                "title":title[:70],
                "company":company,
                "link":j['url'], # Real company apply link
                "desc":desc[:800],
                "qual":qual,"batch":batch,"exp":exp,"loc":loc
            })
        print(f"Real India jobs: {len(jobs)}")
    except Exception as e: print(f"Fetch error {e}")

    # NO FAKE BACKUP - If API fails, post nothing - better than fake
    random.shuffle(jobs)
    return jobs

def is_already_in_blog(company, title):
    try:
        r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=30", timeout=15)
        soup=BeautifulSoup(r.text,'xml')
        for item in soup.find_all('item'):
            t=item.title.text.lower()
            if company.split()[0].lower() in t and title.split()[0].lower() in t:
                return True
    except: pass
    return False

def is_posted(link):
    try:
        with open('posted.json','r') as f: return link in json.load(f)
    except: return False

def save_link(link):
    d=[]
    if os.path.exists('posted.json'):
        try:
            with open('posted.json','r') as f: d=json.load(f)
        except: pass
    d.append(link)
    with open('posted.json','w') as f: json.dump(d[-1000:], f)

def post_blogger(job):
    unique_id = random.randint(1000,9999)
    html=f"""<div style="font-family:Arial;line-height:1.8;"><h1>{job['company']} Hiring {job['title']} - {job['loc']} 2026</h1><p><b>Real Job Alert:</b> {job['company']} hiring {job['title']}.</p><div style="background:#eef2ff;padding:15px;"><p>💼 {job['title']}<br>🏢 {job['company']}<br>🎓 {job['qual']}<br>🔹 {job['batch']}<br>🆕 {job['exp']}<br>📍 {job['loc']}</p></div><p>{job['desc']}</p><p>Apply via official company career site.</p><div style="text-align:center;margin:20px;"><a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:16px 45px;text-decoration:none;border-radius:8px;font-weight:bold;">🌐 Apply Here - Official Link</a></div></div>"""
    msg=MIMEText(html,"html")
    msg['Subject']=f"{job['company']} {job['title']} {job['loc']} {unique_id}"
    msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
            s.login(YOUR_GMAIL, APP_PASSWORD); s.send_message(msg)
        print(f"POSTED REAL: {job['company']}")
        return True
    except Exception as e:
        print(f"BLOGGER FAIL: {e}"); return False

def get_blog_url(job):
    time.sleep(80)
    try:
        r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=10", timeout=15)
        soup=BeautifulSoup(r.text,'xml')
        for item in soup.find_all('item'):
            if job['company'].split()[0].lower() in item.title.text.lower():
                return item.find('link').text
        return soup.find('item').find('link').text
    except: return BLOG_URL

def post_telegram(job, url):
    text=f"""🔥 {job['company']} Off Campus Drive 2026

💼 Job Role: {job['title']}
🏢 Company: {job['company']}
🎓 Qualification: {job['qual']}
🔹 Batch: {job['batch']}
🆕 Experience: {job['exp']}
📍 Location: {job['loc']}

🌐 Apply Here:
{url}

━━━━━━━━━━━━━━━━━━━━
📢 Join Our Telegram Channel
https://t.me/HydHireHub

🌐 Visit Our Blog
https://hydhirehub.blogspot.com
"""
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHANNEL_ID, "text":text})

jobs=fetch_real_jobs()
if not jobs:
    print("No real jobs today - skipping to avoid fake")
    exit()

for job in jobs:
    if is_posted(job['link']): continue
    if is_already_in_blog(job['company'], job['title']):
        save_link(job['link']); continue
    if post_blogger(job):
        url=get_blog_url(job)
        post_telegram(job, url)
        save_link(job['link'])
        print("DONE - Real job posted")
        break
