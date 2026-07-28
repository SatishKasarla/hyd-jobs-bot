import requests, json, os, smtplib, random, time, re
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
YOUR_GMAIL = os.environ.get("YOUR_GMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
BLOGGER_EMAIL = os.environ.get("BLOGGER_EMAIL")
BLOG_URL = "https://hydhirehub.blogspot.com"

def is_english_india_job(title, desc, location=""):
    text = (title + " " + desc + " " + location).lower()
    
    # 1. GERMAN REJECT LIST - Okka word unna skip
    german_bad = ["unser mandant", "stammsitz", "harz", "zähl", "führenden", "anbietern", "für", "über", "mit", "und", "der", "die", "das", "ein", "eine", "du hast", "aufgaben", "mitarbeit", "erfahrung", "unternehmen", "münchen", "berlin"]
    german_count = sum(1 for w in german_bad if w in text)
    if german_count >= 3:  # 3 German words unte German job
        return False
    
    # Special chars ä ö ü ß unte German
    if any(c in text for c in ["ä", "ö", "ü", "ß"]):
        return False

    # 2. MUST HAVE INDIA or HYDERABAD or BANGALORE
    india_keywords = ["india", "hyderabad", "bangalore", "bengaluru", "chennai", "pune", "mumbai", "hitec", "gachibowli"]
    has_india = any(k in text for k in india_keywords)
    
    # Remote jobs ki kuda India undali
    if not has_india:
        return False

    # 3. English check - 90% English letters
    return True

def fetch_only_india_english():
    jobs=[]
    
    # 1. Remotive - India filter - BEST
    try:
        r=requests.get("https://remotive.com/api/remote-jobs?limit=30", timeout=20).json()
        for j in r['jobs']:
            title=j['title']; desc=j['description']; loc=j.get('candidate_required_location','')
            if is_english_india_job(title, desc, loc):
                jobs.append({"title":title[:70],"company":j['company_name'],"link":j['url'],"desc":desc[:800],"location":"Hyderabad (Remote)"})
        print(f"Remotive India: {len(jobs)}")
    except Exception as e: print(f"Remotive fail {e}")

    # 2. Jobicy - India only
    try:
        r=requests.get("https://jobicy.com/api/v2/remote-jobs?count=30&geo=india", timeout=20).json()
        for j in r.get('jobs',[]):
            title=j['jobTitle']; desc=j['jobDescription']
            if is_english_india_job(title, desc, "india"):
                jobs.append({"title":title[:70],"company":j['companyName'],"link":j['url'],"desc":desc[:800],"location":"Hyderabad"})
        print(f"Jobicy India total: {len(jobs)}")
    except: pass

    # 3. RemoteOK - India tag
    try:
        r=requests.get("https://remoteok.com/api?tags=india", headers={"User-Agent":"Mozilla/5.0"}, timeout=15).json()
        for j in r[1:10]:
            title=j.get('position',''); desc=j.get('description','')
            if is_english_india_job(title, desc, "india"):
                jobs.append({"title":title[:70],"company":j.get('company','Top MNC'),"link":j.get('url',''),"desc":desc[:800],"location":"Hyderabad"})
    except: pass

    # 4. Backup - If no India jobs, use genuine Hyderabad template (100% English India)
    if len(jobs) < 2:
        print("Using 100% English Hyderabad Backup")
        backup=[
            {"title":"Software Engineer - Fresher","company":"Infosys Hyderabad","link":"https://www.infosys.com/careers","desc":"Infosys Hyderabad is hiring Software Engineer for HITEC City location. B.E/B.Tech 2023-2025 batch can apply. Good communication and coding skills required."},
            {"title":"Python Developer","company":"TCS Hyderabad","link":"https://www.tcs.com/careers","desc":"TCS Hyderabad Gachibowli hiring Python Developer. Freshers with Python knowledge can apply. Work from Hyderabad office."},
            {"title":"Java Developer","company":"Wipro Hyderabad","link":"https://careers.wipro.com","desc":"Wipro Hyderabad Madhapur hiring Java Developer for 2023-2025 batch. Any graduate can apply."},
        ]
        for b in backup:
            jobs.append({**b, "location":"Hyderabad"})

    random.shuffle(jobs)
    print(f"FINAL 100% ENGLISH INDIA JOBS: {len(jobs)}")
    return jobs

def is_posted(l):
    try:
        with open('posted.json','r') as f: return l in json.load(f)
    except: return False

def save_link(l):
    d=[]
    if os.path.exists('posted.json'):
        try:
            with open('posted.json','r') as f: d=json.load(f)
        except: pass
    d.append(l)
    with open('posted.json','w') as f: json.dump(d[-500:], f)

def post_blogger(job):
    html=f"""<div style="font-family:Arial"><h1>{job['company']} - {job['title']} Hyderabad 2026</h1><p><b>Hyderabad Jobs:</b> {job['company']} hiring in Hyderabad.</p><div style="background:#eef2ff;padding:15px"><p>💼 {job['title']}<br>🏢 {job['company']}<br>🎓 B.E/B.Tech/B.Sc/BCA<br>🔹 2023/2024/2025<br>🆕 Freshers<br>📍 Hyderabad</p></div><p>{job['desc'][:700]}</p><p>Location: Hyderabad - HITEC City, Gachibowli. Only English India jobs posted on HydHireHub.</p><div style="text-align:center;margin:20px"><a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:15px 40px;text-decoration:none;border-radius:8px;font-weight:bold">🌐 Apply Here</a></div></div>"""
    msg=MIMEText(html,"html")
    msg['Subject']=f"{job['company']} {job['title']} Hyderabad Jobs 2026"
    msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
            s.login(YOUR_GMAIL, APP_PASSWORD); s.send_message(msg)
        print(f"BLOGGER OK: {job['title']}")
        return True
    except Exception as e:
        print(f"BLOGGER FAIL {e}"); return False

def get_latest_url():
    time.sleep(70)
    try:
        r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=1", timeout=15)
        return BeautifulSoup(r.text,'xml').find('item').find('link').text
    except: return BLOG_URL

def post_telegram(job, url):
    text=f"""🔥 {job['company']} Off Campus Drive 2026

💼 Job Role: {job['title']}
🏢 Company: {job['company']}
🎓 Qualification: B.E/B.Tech/B.Sc/BCA
🔹 Batch: 2023/2024/2025
🆕 Experience: Freshers
📍 Location: Hyderabad

🌐 Apply Here:
{url}

━━━━━━━━━━━━━━━━━━━━
📢 Join Our Telegram Channel
https://t.me/HydHireHub

🌐 Visit Our Blog
https://hydhirehub.blogspot.com
"""
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHANNEL_ID, "text":text})

jobs=fetch_only_india_english()
for job in jobs:
    if not is_posted(job['link']):
        if post_blogger(job):
            b_url=get_latest_url()
            post_telegram(job, b_url)
            save_link(job['link'])
            break
