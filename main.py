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
    try:
        r=requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=15).json()
        for j in r['data']:
            t=j['title'].lower()
            if any(k in t for k in ['developer','engineer','python','java','react','backend','frontend','intern','analyst','devops']):
                jobs.append({"title":j['title'], "company":j['company_name'], "link":j['url'], "desc":j['description'][:600], "type":j.get('job_types','Full Time')})
    except Exception as e: print(f"ArbeitNow Error {e}")
    try:
        r=requests.get("https://remotive.com/api/remote-jobs?limit=20", timeout=15).json()
        for j in r['jobs']:
            jobs.append({"title":j['title'], "company":j['company_name'], "link":j['url'], "desc":j['description'][:600], "type":j.get('job_type','Full Time')})
    except Exception as e: print(f"Remotive Error {e}")
    random.shuffle(jobs)
    print(f"Total Fresh Jobs: {len(jobs)}")
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
    <div style="font-family:Arial,sans-serif;line-height:1.6;">
    <h1>{job['title']} at {job['company']} - Hiring 2026</h1>
    <p><b>Company:</b> {job['company']}<br><b>Role:</b> {job['title']}<br><b>Job Type:</b> {job['type']}<br><b>Location:</b> Hyderabad / Remote / Bangalore<br><b>Eligibility:</b> Freshers & Experienced</p>
    <p>{job['desc'][:500]}</p>
    <br>
    <h3>Job Details:</h3>
    <p>This is a great opportunity to work at {job['company']} as {job['title']}. If you are passionate and have relevant skills, apply now. This role is open for 2023, 2024, 2025 batches.</p>
    <p>Salary: As per company standards<br>Qualification: B.E/B.Tech/B.Sc/MCA/Any Graduate</p>
    <br>
    <div style="text-align:center; margin:35px 0;">
    <a href="{job['link']}" style="background:#ff3d00;color:#fff;padding:16px 40px;text-decoration:none;border-radius:8px;font-weight:bold;font-size:19px;display:inline-block;">🚀 Apply Now - Official Site</a>
    <p style="font-size:11px;color:gray;">You will be redirected to official career page</p>
    </div>
    <br>
    <p>🔗 More Jobs: <a href="{BLOG_URL}">{BLOG_URL}</a><br>📢 Telegram: <a href="https://t.me/HydHireHub">https://t.me/HydHireHub</a></p>
    </div>
    """
    msg=MIMEText(html,"html")
    msg['Subject']=f"{job['company']} Hiring {job['title']} 2026 | Hyderabad Jobs"
    msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
            s.login(YOUR_GMAIL, APP_PASSWORD); s.send_message(msg)
        print(f"Blogger OK: {job['title']}")
        return True
    except Exception as e:
        print(f"Blogger FAIL: {e}"); return False

def get_latest_blog_url():
    time.sleep(75)
    try:
        r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=1", timeout=20)
        soup=BeautifulSoup(r.text,'xml')
        item=soup.find('item')
        if item and item.find('link'):
            link=item.find('link').text
            print(f"Blog URL: {link}")
            return link
        return BLOG_URL
    except Exception as e:
        print(f"Blog URL Error: {e}")
        return BLOG_URL

def post_telegram(job, blog_url):
    text=f"""🔥 HIRING: {job['title']}

🏢 Company: {job['company']}
💻 Type: {job['type']}
📍 Location: Hyderabad / Remote

✅ Full Details & Apply:
{blog_url}

#HyderabadJobs #FreshersJobs #SoftwareJobs #HydHireHub
"""
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        resp=requests.post(url, data={"chat_id":CHANNEL_ID, "text":text}, timeout=15)
        print(f"Telegram: {resp.status_code}")
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
            break

if posted==0:
    print("No new jobs to post this time - will get fresh next schedule")
