import requests, json, os, smtplib, random, time
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
    # German reject
    german_bad = ["unser mandant", "stammsitz", "führenden", "anspr", "für", "über", "mit", "und", "der", "die", "das", "unser", "du hast", "aufgaben", "erfahrung", "unternehmen", "münchen"]
    if sum(1 for w in german_bad if w in text) >= 3:
        return False
    if any(c in text for c in ["ä", "ö", "ü", "ß"]):
        return False
    # Must have India
    india_keywords = ["india", "hyderabad", "bangalore", "bengaluru", "chennai", "pune", "mumbai", "hitec", "gachibowli", "telangana"]
    if not any(k in text for k in india_keywords):
        # Remotive lo location remote unna India jobs ye, so allow if source is India API
        if "india" not in location.lower() and "hyderabad" not in location.lower():
            return False
    return True

def fetch_only_india_english():
    jobs=[]
    # 1. Remotive - India
    try:
        r=requests.get("https://remotive.com/api/remote-jobs?limit=30", timeout=20).json()
        for j in r['jobs']:
            if is_english_india_job(j['title'], j['description'], j.get('candidate_required_location','')):
                jobs.append({"title":j['title'][:70],"company":j['company_name'],"link":j['url'],"desc":j['description'][:800],"location":"Hyderabad"})
        print(f"Remotive India: {len(jobs)}")
    except Exception as e: print(f"Remotive fail {e}")

    # 2. Jobicy - India only - BEST
    try:
        r=requests.get("https://jobicy.com/api/v2/remote-jobs?count=30&geo=india", timeout=20).json()
        for j in r.get('jobs',[]):
            if is_english_india_job(j['jobTitle'], j['jobDescription'], "india"):
                jobs.append({"title":j['jobTitle'][:70],"company":j['companyName'],"link":j['url'],"desc":j['jobDescription'][:800],"location":"Hyderabad"})
        print(f"Jobicy India total: {len(jobs)}")
    except Exception as e: print(f"Jobicy fail {e}")

    # 3. RemoteOK India
    try:
        r=requests.get("https://remoteok.com/api?tags=india", headers={"User-Agent":"Mozilla/5.0"}, timeout=15).json()
        for j in r[1:8]:
            if is_english_india_job(j.get('position',''), j.get('description',''), "india"):
                jobs.append({"title":j.get('position','')[:70],"company":j.get('company','Top MNC'),"link":j.get('url',''),"desc":j.get('description','')[:800],"location":"Hyderabad"})
    except: pass

    # 4. Backup Hyderabad - 100% English
    if len(jobs) < 2:
        backup=[
            {"title":"Software Engineer Fresher","company":"Infosys","link":"https://www.infosys.com/careers","desc":"Infosys Hyderabad HITEC City hiring Software Engineer for 2023-2025 batch. B.E/B.Tech can apply."},
            {"title":"Python Developer","company":"TCS","link":"https://www.tcs.com/careers","desc":"TCS Hyderabad Gachibowli hiring Python Developer. Freshers with Python knowledge can apply."},
        ]
        for b in backup: jobs.append({**b, "location":"Hyderabad"})

    random.shuffle(jobs)
    print(f"FINAL ENGLISH INDIA JOBS: {len(jobs)}")
    return jobs[:10]

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
    html=f"""
    <div style="font-family:Arial;line-height:1.8;">
    <h1>{job['company']} Hiring {job['title']} - Hyderabad Jobs 2026</h1>
    <p><b>HydHireHub Hyderabad Jobs:</b> {job['company']} hiring {job['title']} in Hyderabad location.</p>
    <div style="background:#eef2ff;padding:15px;border-radius:8px;">
    <p>💼 Job Role: {job['title']}<br>🏢 Company: {job['company']}<br>🎓 Qualification: B.E/B.Tech/B.Sc/BCA<br>🔹 Batch: 2023/2024/2025<br>🆕 Experience: Freshers<br>📍 Location: Hyderabad</p>
    </div>
    <h3>Job Description:</h3><p>{job['desc'][:800]}</p>
    <p>Work Location: Hyderabad - HITEC City, Gachibowli, Madhapur. Candidates willing to work in Hyderabad can apply.</p>
    <div style="text-align:center;margin:30px 0;">
    <a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:16px 45px;text-decoration:none;border-radius:8px;font-weight:bold;font-size:18px;">🌐 Apply Here - Original Company Link</a>
    </div>
    </div>
    """
    msg=MIMEText(html,"html")
    msg['Subject']=f"{job['company']} Off Campus Drive - {job['title']} Hyderabad 2026"
    msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
            s.login(YOUR_GMAIL, APP_PASSWORD); s.send_message(msg)
        print(f"BLOGGER POSTED: {job['company']} - {job['title']}")
        return True
    except Exception as e:
        print(f"BLOGGER FAIL {e}"); return False

def get_latest_url(job):
    print(f"Waiting for Blogger: {job['company']}")
    time.sleep(90)
    for attempt in range(3):
        try:
            r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=10", timeout=15)
            soup=BeautifulSoup(r.text,'xml')
            items=soup.find_all('item')
            # Find exact match
            for item in items:
                t=item.title.text.lower()
                if job['company'].split()[0].lower() in t:
                    url=item.find('link').text
                    print(f"CORRECT URL FOUND: {url}")
                    return url
            if items:
                return items[0].find('link').text
        except Exception as e:
            print(f"RSS try {attempt} fail {e}")
        time.sleep(20)
    return BLOG_URL

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
        print("TELEGRAM OK - Correct URL")
    except Exception as e: print(f"Telegram fail {e}")

# MAIN RUN
jobs=fetch_only_india_english()
posted=False
for job in jobs:
    if not is_posted(job['link']):
        if post_blogger(job):
            b_url=get_latest_url(job)
            post_telegram(job, b_url)
            save_link(job['link'])
            posted=True
            break

if not posted:
    print("No new job - all posted")
