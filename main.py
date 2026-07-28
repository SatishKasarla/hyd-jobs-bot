import requests, json, os, smtplib, random, time
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
YOUR_GMAIL = os.environ.get("YOUR_GMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
BLOGGER_EMAIL = os.environ.get("BLOGGER_EMAIL")
BLOG_URL = "https://hydhirehub.blogspot.com"

def fetch_all_hyd_jobs():
    jobs=[]
    headers={"User-Agent":"Mozilla/5.0"}

    # 1. Remotive - 100% Works on GitHub
    try:
        r=requests.get("https://remotive.com/api/remote-jobs?limit=20", timeout=15).json()
        for j in r['jobs']:
            if "india" in j.get('candidate_required_location','').lower() or "asia" in j.get('candidate_required_location','').lower():
                if "Du hast" not in j['title']:
                    jobs.append({"title":j['title'][:70],"company":j['company_name'],"link":j['url'],"desc":j['description'][:800],"location":"Hyderabad (Remote)"})
        print(f"Remotive: {len(jobs)}")
    except Exception as e: print(f"Remotive fail {e}")

    # 2. Jobicy API - Works
    try:
        r=requests.get("https://jobicy.com/api/v2/remote-jobs?count=20&geo=india", timeout=15).json()
        for j in r.get('jobs',[]):
            jobs.append({"title":j['jobTitle'][:70],"company":j['companyName'],"link":j['url'],"desc":j['jobDescription'][:800],"location":"Hyderabad"})
        print(f"Jobicy: added")
    except: pass

    # 3. ArbeitNow - Works
    try:
        r=requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=15).json()
        for j in r['data'][:10]:
            if "Du hast" not in j['title']:
                jobs.append({"title":j['title'][:70],"company":j['company_name'],"link":j['url'],"desc":j['description'][:800],"location":"Hyderabad"})
        print(f"ArbeitNow: added")
    except: pass

    # 4. Indeed Hyderabad - Try (sometimes GitHub blocks, but try)
    try:
        url="https://rss.indeed.com/rss?q=software&l=Hyderabad"
        r=requests.get(url, headers=headers, timeout=12)
        soup=BeautifulSoup(r.text,'xml')
        for item in soup.find_all('item')[:4]:
            title=item.title.text.split('-')[0].strip()
            if "Du hast" not in title:
                jobs.append({"title":title[:70],"company":"Top MNC Hyderabad","link":item.link.text,"desc":BeautifulSoup(item.description.text,'html.parser').get_text()[:800],"location":"Hyderabad"})
        print(f"Indeed Hyd: tried")
    except: pass

    # 5. Internshala Alternative - RemoteOK India
    try:
        r=requests.get("https://remoteok.com/api?tags=india", headers=headers, timeout=15).json()
        for j in r[1:6]:
            jobs.append({"title":j['position'][:70],"company":j['company'],"link":j['url'],"desc":j.get('description','')[:800],"location":"Hyderabad"})
    except: pass

    # Filter English only
    final=[]
    for job in jobs:
        if "Du hast" not in job['title'] and "Aufgaben" not in job['desc']:
            final.append(job)

    random.shuffle(final)
    print(f"TOTAL MULTI-PORTAL HYD JOBS: {len(final)}")
    return final[:10]

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
    html=f"""<div style="font-family:Arial;line-height:1.8;">
    <h1>{job['company']} - {job['title']} Hyderabad Jobs 2026</h1>
    <p><b>Hyderabad Jobs:</b> {job['company']} hiring {job['title']} in Hyderabad.</p>
    <div style="background:#eef2ff;padding:15px;"><p>💼 {job['title']}<br>🏢 {job['company']}<br>🎓 B.E/B.Tech/B.Sc/BCA<br>🔹 2023/2024/2025<br>🆕 Freshers<br>📍 Hyderabad</p></div>
    <p>{job['desc'][:600]}</p>
    <p>Location: Hyderabad HITEC City, Gachibowli. Apply fast.</p>
    <div style="text-align:center;margin:20px;"><a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:15px 40px;text-decoration:none;border-radius:8px;font-weight:bold;">🌐 Apply Here - Hyderabad</a></div></div>"""
    msg=MIMEText(html,"html")
    msg['Subject']=f"{job['company']} Hiring {job['title']} Hyderabad 2026"
    msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
            s.login(YOUR_GMAIL, APP_PASSWORD); s.send_message(msg)
        print(f"POSTED BLOGGER: {job['title']} from {job['company']}")
        return True
    except Exception as e:
        print(f"BLOGGER FAIL {e}"); return False

def get_latest_url():
    time.sleep(65)
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

jobs=fetch_all_hyd_jobs()
for job in jobs:
    if not is_posted(job['link']):
        if post_blogger(job):
            b_url=get_latest_url()
            post_telegram(job, b_url)
            save_link(job['link'])
            print("DONE")
            break
