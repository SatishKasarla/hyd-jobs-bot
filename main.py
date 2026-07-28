import requests, json, os, smtplib, random, time
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
YOUR_GMAIL = os.environ.get("YOUR_GMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
BLOGGER_EMAIL = os.environ.get("BLOGGER_EMAIL")
BLOG_URL = "https://hydhirehub.blogspot.com"

def get_only_hyd_jobs():
    jobs=[]
    headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # 1. Indeed Hyderabad - 100% Working
    try:
        url="https://rss.indeed.com/rss?q=software+developer&l=Hyderabad&sort=date"
        r=requests.get(url, headers=headers, timeout=15)
        soup=BeautifulSoup(r.text, 'xml')
        for item in soup.find_all('item')[:5]:
            jobs.append({
                "title": item.title.text.split('-')[0].strip()[:80],
                "company": "Top MNC in Hyderabad",
                "link": item.link.text,
                "desc": BeautifulSoup(item.description.text, 'html.parser').get_text()[:800],
                "location": "Hyderabad"
            })
        print(f"Indeed Hyd: {len(jobs)} jobs")
    except Exception as e:
        print(f"Indeed Error {e}")

    # 2. Indeed Hyderabad - Fresher
    try:
        url="https://rss.indeed.com/rss?q=fresher&l=Hyderabad&sort=date"
        r=requests.get(url, headers=headers, timeout=15)
        soup=BeautifulSoup(r.text, 'xml')
        for item in soup.find_all('item')[:5]:
            jobs.append({
                "title": item.title.text.split('-')[0].strip()[:80],
                "company": "MNC Hiring in Hyderabad",
                "link": item.link.text,
                "desc": BeautifulSoup(item.description.text, 'html.parser').get_text()[:800],
                "location": "Hyderabad"
            })
    except: pass

    # 3. Backup - ArbeitNow Remote as Hyderabad Remote (AdSense ki genuine)
    if len(jobs) < 3:
        try:
            r=requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=15).json()
            for j in r['data'][:5]:
                jobs.append({
                    "title": j['title'],
                    "company": j['company_name'],
                    "link": j['url'],
                    "desc": j['description'][:800],
                    "location": "Hyderabad (Remote)"
                })
        except: pass

    random.shuffle(jobs)
    print(f"TOTAL HYD JOBS READY: {len(jobs)}")
    return jobs

def is_posted(link):
    try:
        with open('posted.json','r') as f:
            return link in json.load(f)
    except: return False

def save_link(link):
    data=[]
    if os.path.exists('posted.json'):
        try:
            with open('posted.json','r') as f: data=json.load(f)
        except: pass
    data.append(link)
    with open('posted.json','w') as f: json.dump(data[-300:], f)

def post_blogger(job):
    html=f"""
    <div style="font-family:Arial;line-height:1.8;">
    <h1>{job['company']} - {job['title']} Jobs in Hyderabad 2026</h1>
    <p><b>Hyderabad Jobs 2026:</b> {job['company']} hiring {job['title']} in Hyderabad. Excellent opportunity for freshers and experienced.</p>
    <div style="background:#e8f0fe;padding:15px;border-radius:8px;">
    <p>💼 Job Role: {job['title']}<br>
    🏢 Company: {job['company']}<br>
    🎓 Qualification: B.E/B.Tech/B.Sc/BCA/MCA/Any Graduate<br>
    🔹 Batch: 2023/2024/2025/2026<br>
    🆕 Experience: Freshers & Experienced<br>
    📍 Location: Hyderabad<br>
    💰 Salary: Best in Industry (Hyderabad Standards)</p>
    </div>
    <h3>Job Description - Hyderabad Location:</h3>
    <p>{job['desc']}</p>
    <p>This job is based in Hyderabad. Candidates from Hyderabad or willing to relocate to Hyderabad can apply. Great chance to work in Hyderabad's top IT hub - HITEC City, Gachibowli, Madhapur area.</p>
    <h3>How to Apply for Hyderabad Jobs?</h3>
    <div style="text-align:center;margin:30px 0;">
    <a href="{job['link']}" style="background:#ff3d00;color:#fff;padding:16px 45px;text-decoration:none;border-radius:8px;font-weight:bold;font-size:18px;">🌐 Apply Here - Hyderabad Jobs</a>
    </div>
    <p>More Hyderabad Jobs: {BLOG_URL} | Telegram: https://t.me/HydHireHub</p>
    </div>
    """
    msg=MIMEText(html,"html")
    msg['Subject']=f"{job['title']} - {job['company']} Hyderabad Jobs 2026"
    msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
            s.login(YOUR_GMAIL, APP_PASSWORD); s.send_message(msg)
        print(f"Blogger OK: {job['title']} Hyd")
        return True
    except Exception as e:
        print(f"Blogger FAIL {e}"); return False

def get_latest_blog_url():
    time.sleep(75)
    try:
        r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=1", timeout=20)
        soup=BeautifulSoup(r.text,'xml')
        link=soup.find('item').find('link').text
        print(f"Blog URL: {link}")
        return link
    except:
        return BLOG_URL

def post_telegram(job, blog_url):
    text=f"""🔥 {job['company']} Off Campus Drive 2026

💼 Job Role: {job['title']}
🏢 Company: {job['company']}
🎓 Qualification: B.E/B.Tech/B.Sc/BCA
🔹 Batch: 2023/2024/2025/2026
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
        resp=requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHANNEL_ID, "text":text}, timeout=15)
        print(f"Telegram Status: {resp.status_code}")
    except Exception as e:
        print(f"Telegram Error {e}")

jobs=get_only_hyd_jobs()
if not jobs:
    print("No jobs fetched - check Indeed RSS")
else:
    posted=False
    for job in jobs:
        if not is_posted(job['link']):
            if post_blogger(job):
                b_url=get_latest_blog_url()
                post_telegram(job, b_url)
                save_link(job['link'])
                posted=True
                break
    if not posted:
        print("All jobs already posted, will post next hour new ones")
