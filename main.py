import requests, json, os, smtplib, random, time
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
YOUR_GMAIL = os.environ.get("YOUR_GMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
BLOGGER_EMAIL = os.environ.get("BLOGGER_EMAIL")
BLOG_URL = "https://hydhirehub.blogspot.com"

def get_india_worldwide_jobs():
    jobs=[]
    headers = {"User-Agent":"Mozilla/5.0"}

    # 1. Indeed India - Hyderabad, Chennai, Pune, Mumbai, Bangalore
    for city in ["Hyderabad", "Chennai", "Pune", "Mumbai", "Bangalore"]:
        try:
            url = f"https://rss.indeed.com/rss?q=&l={city}&sort=date"
            r = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(r.text, 'xml')
            for item in soup.find_all('item')[:2]:
                jobs.append({
                    "title": item.title.text[:80],
                    "company": "Top MNC",
                    "link": item.link.text,
                    "desc": item.description.text[:700],
                    "type": "Full Time",
                    "location": city,
                    "salary": "Not Disclosed"
                })
        except: pass

    # 2. ArbeitNow - Worldwide
    try:
        r=requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=20).json()
        for j in r['data'][:10]:
            if any(k in j['title'].lower() for k in ['developer','engineer','analyst','python','java','walk','support','manager','designer']):
                jobs.append({
                    "title": j['title'],
                    "company": j['company_name'],
                    "link": j['url'],
                    "desc": j['description'][:700],
                    "type": j.get('job_types','Full Time'),
                    "location": j.get('location','Remote - Worldwide'),
                    "salary": j.get('salary','Not Disclosed') or "Not Disclosed"
                })
    except: pass

    # 3. Remotive Remote
    try:
        r=requests.get("https://remotive.com/api/remote-jobs?limit=15", timeout=20).json()
        for j in r['jobs'][:5]:
            jobs.append({
                "title": j['title'],
                "company": j['company_name'],
                "link": j['url'],
                "desc": j['description'][:700],
                "type": j.get('job_type','Remote'),
                "location": "Worldwide Remote",
                "salary": j.get('salary','Not Disclosed')
            })
    except: pass

    random.shuffle(jobs)
    print(f"Total India+Worldwide Jobs: {len(jobs)}")
    return jobs[:8]

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
    with open('posted.json','w') as f: json.dump(data[-400:], f)

def post_blogger(job):
    html=f"""
    <div style="font-family:Arial;line-height:1.7;">
    <h1>{job['title']} - {job['company']} Hiring in {job['location']}</h1>
    <div style="background:#eef2ff;padding:15px;border-left:4px solid #0d6efd;">
    <p><b>🏢 Company:</b> {job['company']}<br>
    <b>💼 Role:</b> {job['title']}<br>
    <b>📍 Location:</b> {job['location']}<br>
    <b>💰 Salary:</b> {job['salary']}<br>
    <b>📋 Job Type:</b> {job['type']} | Walk-in / Full Time / Remote<br>
    <b>🎓 Eligibility:</b> Any Graduate / Freshers</p>
    </div>
    <p>{job['desc'][:800]}</p>
    <div style="text-align:center;margin:30px 0;">
    <a href="{job['link']}" style="background:#ff3d00;color:#fff;padding:16px 45px;text-decoration:none;border-radius:8px;font-weight:bold;font-size:19px;">🚀 Apply Now - Official Link</a>
    </div>
    <p>More: {BLOG_URL} | Telegram: https://t.me/HydHireHub</p>
    </div>
    """
    msg=MIMEText(html,"html")
    msg['Subject']=f"{job['title']} in {job['location']} - {job['company']} Hiring"
    msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
            s.login(YOUR_GMAIL, APP_PASSWORD); s.send_message(msg)
        print(f"Blogger OK: {job['title']} - {job['location']}")
        return True
    except Exception as e:
        print(f"Blogger FAIL {e}"); return False

def get_latest_blog_url():
    time.sleep(80)
    try:
        r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=1", timeout=20)
        soup=BeautifulSoup(r.text,'xml')
        item=soup.find('item')
        return item.find('link').text if item else BLOG_URL
    except: return BLOG_URL

def post_telegram(job, blog_url):
    text=f"""💼 {job['title']}

🏢 {job['company']}
📍 {job['location']}
💰 {job['salary']}
📋 {job['type']}

🔗 Details & Apply:
{blog_url}

#{job['location'].replace(' ','')}Jobs #WalkinJobs #HydHireHub
"""
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHANNEL_ID, "text":text}, timeout=15)
    except: pass

jobs=get_india_worldwide_jobs()
for job in jobs:
    if not is_posted(job['link']):
        if post_blogger(job):
            b_url=get_latest_blog_url()
            post_telegram(job, b_url)
            save_link(job['link'])
            break
