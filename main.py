import requests, json, os, smtplib, random, time
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
YOUR_GMAIL = os.environ.get("YOUR_GMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
BLOGGER_EMAIL = os.environ.get("BLOGGER_EMAIL")
BLOG_URL = "https://hydhirehub.blogspot.com"

def get_fresh_jobs():
    jobs=[]
    # 1. ArbeitNow - Daily fresh jobs
    try:
        r=requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=15).json()
        for j in r['data']:
            t=j['title'].lower()
            if any(k in t for k in ['developer','engineer','python','java','react','intern','analyst']):
                jobs.append({"title":j['title'], "company":j['company_name'], "link":j['url'], "desc":j['description'][:400], "type":j.get('job_types','')})
    except: pass
    # 2. Remotive
    try:
        r=requests.get("https://remotive.com/api/remote-jobs?limit=20", timeout=15).json()
        for j in r['jobs']:
            jobs.append({"title":j['title'], "company":j['company_name'], "link":j['url'], "desc":j['description'][:400], "type":j.get('job_type','')})
    except: pass

    random.shuffle(jobs)
    print(f"Total Fresh Jobs Fetched: {len(jobs)}")
    return jobs[:5]

def is_posted(link):
    try:
        with open('posted.json','r') as f: return link in json.load(f)
    except: return False

def save_link(link):
    data=[]
    if os.path.exists('posted.json'):
        try:
            with open('posted.json','r') as f: data=json.load(f)
        except: pass
    data.append(link)
    with open('posted.json','w') as f: json.dump(data[-200:], f)

def post_blogger(job):
    html=f"""
    <h2>{job['title']} at {job['company']} - {job['type']} | Hyderabad</h2>
    <p><b>Company:</b> {job['company']}<br><b>Role:</b> {job['title']}<br><b>Type:</b> {job['type']}<br><b>Location:</b> Remote / Hyderabad</p>
    <p>{job['desc']}</p>
    <p><a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:12px 25px;text-decoration:none;border-radius:6px;display:inline-block;">Apply Now</a></p>
    <p><br>More Jobs: {BLOG_URL} | Telegram: https://t.me/HydHireHub</p>"""
    msg=MIMEText(html,"html")
    msg['Subject']=f"{job['title']} - {job['company']} Hiring 2026"
    msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
            s.login(YOUR_GMAIL, APP_PASSWORD); s.send_message(msg)
        print(f"Blogger OK: {job['title']}")
        return True
    except Exception as e:
        print(f"Blogger FAIL: {e}"); return False

def get_latest_blog_url():
    time.sleep(70)
    try:
        r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=1", timeout=15)
        soup=BeautifulSoup(r.text,'xml')
        item=soup.find('item')
        link=item.find('link').text if item else BLOG_URL
        print(f"Blog URL Found: {link}")
        return link
    except Exception as e:
        print(f"Blog URL Error: {e}")
        return BLOG_URL

def post_telegram(job, blog_url):
    # DYNAMIC TITLE - Off Campus word ledu, original title eh
    text=f"""💼 {job['title']}

🏢 Company: {job['company']}
💻 Role Type: {job['type'] if job['type'] else 'Full Time'}
📍 Location: Hyderabad / Remote

📄 Job Details & Official Apply:
{blog_url}

🔗 Direct Apply is inside blog post

━━━━━━━━━━━━━━
@HydHireHub | {BLOG_URL}
"""
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        resp=requests.post(url, data={"chat_id":CHANNEL_ID, "text":text}, timeout=15)
        print(f"Telegram Status: {resp.status_code}")
    except Exception as e:
        print(f"Telegram Error: {e}")

jobs=get_fresh_jobs()
posted=0
for job in jobs:
    if not is_posted(job['link']):
        if post_blogger(job):
            b_url=get_latest_blog_url()
            post_telegram(job, b_url)
            save_link(job['link'])
            posted+=1
            if posted>=1: break

if posted==0:
    print("No fresh jobs - will try next schedule")
