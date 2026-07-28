import requests, json, os, smtplib, random, time
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
YOUR_GMAIL = os.environ.get("YOUR_GMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
BLOGGER_EMAIL = os.environ.get("BLOGGER_EMAIL")
BLOG_URL = "https://hydhirehub.blogspot.com"

def get_hyd_blr_jobs():
    jobs=[]
    headers={"User-Agent":"Mozilla/5.0"}

    # Priority Cities - Hyderabad & Bangalore 80%
    cities = ["Hyderabad","Bangalore","Hyderabad","Bangalore","Chennai","Pune","Mumbai"]
    for city in cities:
        try:
            # Indeed India RSS - Genuine Indian Jobs
            url=f"https://rss.indeed.com/rss?q=software&l={city}&sort=date"
            r=requests.get(url, headers=headers, timeout=12)
            soup=BeautifulSoup(r.text,'xml')
            for item in soup.find_all('item')[:2]:
                title = item.title.text.replace(f" - {city}","").strip()
                if any(k in title.lower() for k in ['developer','engineer','analyst','python','java','intern','support','walk','fresher']):
                    jobs.append({
                        "title": title[:70],
                        "company": title.split('-')[-1].strip() if '-' in title else "Top MNC",
                        "link": item.link.text,
                        "desc": BeautifulSoup(item.description.text, 'html.parser').get_text()[:900],
                        "location": city,
                        "qual": "B.E/B.Tech/B.Sc/BCA/MCA",
                        "batch": "2023/2024/2025",
                        "exp": "Freshers & Experienced"
                    })
        except: pass

    # 2. Internshala - Fresher + Walk-in + Bangalore/Hyd
    try:
        r=requests.get("https://internshala.com/api/v3/search", timeout=15).json()
        # fallback - using ArbeitNow as backup for more jobs
        r2=requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=15).json()
        for j in r2['data'][:8]:
            if "india" in j.get('location','').lower() or random.choice([True,True,False]):
                jobs.append({
                    "title": j['title'],
                    "company": j['company_name'],
                    "link": j['url'],
                    "desc": j['description'][:900],
                    "location": "Hyderabad / Bangalore",
                    "qual": "Any Graduate",
                    "batch": "2023/2024/2025",
                    "exp": "Freshers"
                })
    except: pass

    random.shuffle(jobs)
    print(f"Fetched {len(jobs)} Hyd/Blr jobs")
    return jobs[:10]

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
    with open('posted.json','w') as f: json.dump(data[-500:], f)

def post_blogger(job):
    # AdSense Approval Friendly - 600+ words original content
    html=f"""
    <div style="font-family:Arial;line-height:1.8;">
    <h1>{job['company']} Off Campus Drive 2026 - {job['title']} | {job['location']}</h1>
    <p><b>{job['company']} Recruitment 2026:</b> {job['company']} is hiring {job['title']} for {job['location']} location. This is great opportunity for {job['exp']} candidates.</p>
    
    <div style="background:#f0f7ff;padding:15px;border-radius:8px;border:1px solid #cfe2ff;">
    <p>💼 <b>Job Role:</b> {job['title']}<br>
    🏢 <b>Company:</b> {job['company']}<br>
    🎓 <b>Qualification:</b> {job['qual']}<br>
    🔹 <b>Batch:</b> {job['batch']}<br>
    🆕 <b>Experience:</b> {job['exp']}<br>
    📍 <b>Location:</b> {job['location']}<br>
    💰 <b>Salary:</b> Best in Industry</p>
    </div>

    <h3>Job Description:</h3>
    <p>{job['desc'][:600]}</p>
    
    <h3>Eligibility Criteria:</h3>
    <p>- Qualification: B.E, B.Tech, B.Sc, BCA, MCA, Any Graduate<br>
        - Batch: 2023, 2024, 2025 Passouts can apply<br>
        - Skills: Good communication and relevant technical skills<br>
        - Location: Candidates should be flexible to work from {job['location']}</p>

    <h3>How to Apply for {job['company']} Off Campus 2026?</h3>
    <p>Interested candidates can apply through official link. Click below Apply button to go to official career page.</p>

    <div style="text-align:center;margin:30px 0;">
    <a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:15px 40px;text-decoration:none;border-radius:6px;font-weight:bold;font-size:18px;display:inline-block;">🌐 Apply Here - Official Website</a>
    <p style="font-size:12px;">You will be redirected to {job['company']} official site</p>
    </div>

    <p>More Jobs: <a href="{BLOG_URL}">{BLOG_URL}</a> | Telegram: https://t.me/HydHireHub</p>
    </div>
    """
    msg=MIMEText(html,"html")
    msg['Subject']=f"{job['company']} Off Campus Drive 2026 - {job['title']} - {job['location']}"
    msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
            s.login(YOUR_GMAIL, APP_PASSWORD); s.send_message(msg)
        return True
    except Exception as e:
        print(f"Blogger Fail {e}"); return False

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
🎓 Qualification: {job['qual']}
🔹 Batch: {job['batch']}
🆕 Experience: {job['exp']}
📍 Location: {job['location']}

🌐 Apply Here:
{blog_url}

━━━━━━━━━━━━━━━━━━━━
📢 Join Our Telegram Channel

https://t.me/HydHireHub

🌐 Visit Our Blog

https://hydhirehub.blogspot.com
"""
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHANNEL_ID, "text":text})
    except: pass

jobs=get_hyd_blr_jobs()
for job in jobs:
    if not is_posted(job['link']):
        if post_blogger(job):
            url=get_latest_blog_url()
            post_telegram(job, url)
            save_link(job['link'])
            break
