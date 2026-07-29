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

# Known MNCs - Channel lo trust kosam
MNC_LIST = ["TCS", "Infosys", "Wipro", "Cognizant", "Accenture", "Capgemini", "Tech Mahindra", "HCL", "Amazon", "IBM"]

def parse_details(desc, title):
    text = (title + " " + desc).lower()
    # Qualification - dynamic
    if "mba" in text: qual = "B.E/B.Tech/MBA/MCA"
    elif "bca" in text or "bsc" in text: qual = "B.E/B.Tech/B.Sc/BCA/MCA"
    else: qual = "B.E/B.Tech/M.Tech/MCA"

    # Batch - dynamic from description
    years = re.findall(r'20(?:2[3-6])', text)
    if years:
        uniq = sorted(list(set(years)))[:3]
        batch = "/".join(uniq)
    else:
        batch = "2024/2025/2026" if random.random()>0.5 else "2023/2024/2025"

    # Experience - dynamic
    if "0-1" in text or "fresher" in text or "0 year" in text: exp = "Freshers (0-1 Year)"
    elif "1-2" in text or "2 year" in text: exp = "0-2 Years"
    elif "3" in text and "5" in text: exp = "2-5 Years"
    else: exp = "Freshers"

    # Location - Remote vs Hyd - dynamic
    if "remote" in text and "hyderabad" not in text: loc = "Remote (India)"
    elif "bangalore" in text and "hyderabad" not in text: loc = "Bangalore"
    elif "pune" in text: loc = "Pune / Hyderabad"
    else: loc = "Hyderabad"

    return qual, batch, exp, loc

def fetch_jobs():
    jobs=[]
    try:
        # Jobicy India - most reliable
        r=requests.get("https://jobicy.com/api/v2/remote-jobs?count=30&geo=india", timeout=20).json()
        for j in r.get('jobs',[]):
            desc=j.get('jobDescription','')
            title=j.get('jobTitle','')
            # Skip German
            if any(x in title.lower() for x in ["für","unser","ä","ö","ü"]): continue
            # Skip if no India context
            if "india" not in desc.lower() and "hyderabad" not in desc.lower() and "remote" not in desc.lower(): continue

            qual,batch,exp,loc = parse_details(desc, title)
            jobs.append({
                "title":title[:70],
                "company":j['companyName'],
                "link":j['url'],
                "desc":desc[:800],
                "qual":qual,"batch":batch,"exp":exp,"loc":loc
            })
        print(f"Fetched {len(jobs)} dynamic jobs")
    except Exception as e: print(f"Fetch error {e}")

    # Add 1-2 Real MNC template jobs to avoid fake doubt (rotate daily)
    today = datetime.now().day
    if today % 2 == 0:
        jobs.insert(0, {"title":"Associate Software Engineer","company":"Cognizant","link":"https://careers.cognizant.com","desc":"Cognizant Hyderabad hiring Associate Software Engineer for 2024-2026 batch. Good coding skills required. Work from Hyderabad.","qual":"B.E/B.Tech/MCA","batch":"2024/2025/2026","exp":"Freshers","loc":"Hyderabad"})
    else:
        jobs.insert(0, {"title":"System Engineer","company":"TCS","link":"https://www.tcs.com/careers","desc":"TCS Hyderabad off campus drive for 2025 batch. B.E/B.Tech eligible. Location Hyderabad HITEC City.","qual":"B.E/B.Tech/M.Tech","batch":"2025/2026","exp":"Freshers (0 Year)","loc":"Hyderabad"})

    random.shuffle(jobs)
    return jobs[:10]

def is_already_in_blog(company, title):
    # Check RSS if already posted to avoid duplicate
    try:
        r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=20", timeout=15)
        soup=BeautifulSoup(r.text,'xml')
        for item in soup.find_all('item'):
            t=item.title.text.lower()
            if company.split()[0].lower() in t and title.split()[0].lower() in t:
                print(f"Duplicate found in blog: {company} {title}")
                return True
    except: pass
    return False

def is_posted(link):
    try:
        with open('posted.json','r') as f:
            data=json.load(f)
            # Check link or company+title
            return link in data
    except: return False

def save_link(link):
    d=[]
    if os.path.exists('posted.json'):
        try:
            with open('posted.json','r') as f: d=json.load(f)
        except: pass
    d.append(link)
    # Keep last 500 + timestamp
    with open('posted.json','w') as f: json.dump(d[-500:], f)

def post_blogger(job):
    # Unique subject to avoid block
    unique_id = random.randint(100,999)
    html=f"""
    <div style="font-family:Arial;line-height:1.8;">
    <h1>{job['company']} Hiring {job['title']} - {job['loc']} Jobs {datetime.now().year}</h1>
    <p><b>{job['company']} Off Campus Drive:</b> {job['desc'][:500]}</p>
    <div style="background:#eef2ff;padding:15px;border-radius:8px;">
    <p>💼 Job Role: {job['title']}<br>🏢 Company: {job['company']}<br>🎓 Qualification: {job['qual']}<br>🔹 Batch: {job['batch']}<br>🆕 Experience: {job['exp']}<br>📍 Location: {job['loc']}</p>
    </div>
    <h3>Job Details:</h3><p>{job['desc']}</p>
    <p>Location: {job['loc']} - Apply before link expires.</p>
    <div style="text-align:center;margin:30px 0;">
    <a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:16px 45px;text-decoration:none;border-radius:8px;font-weight:bold;">🌐 Apply Here - Company Site</a>
    </div>
    """
    msg=MIMEText(html,"html")
    msg['Subject']=f"{job['company']} {job['title']} {job['loc']} - {unique_id} {datetime.now().strftime('%d %b')}" # Unique subject prevents block
    msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
    # Extra header to avoid spam
    msg['X-Priority']='3'
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
            s.login(YOUR_GMAIL, APP_PASSWORD)
            s.send_message(msg)
        print(f"BLOGGER OK: {job['company']} {job['loc']} {job['batch']}")
        return True
    except Exception as e:
        print(f"BLOGGER BLOCK/FAIL: {e}")
        return False

def get_blog_url(job):
    time.sleep(75)
    try:
        r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=10", timeout=15)
        soup=BeautifulSoup(r.text,'xml')
        for item in soup.find_all('item'):
            if job['company'].split()[0].lower() in item.title.text.lower():
                url=item.find('link').text
                print(f"CORRECT URL: {url}")
                return url
        return soup.find('item').find('link').text
    except: return BLOG_URL

def post_telegram(job, url):
    text=f"""🔥 {job['company']} Off Campus Drive {datetime.now().year}

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

# MAIN - Prevent duplicate + block
jobs=fetch_jobs()
# Check last post time - avoid hourly spam block - post only if 5+ hours gap
try:
    with open('posted.json','r') as f: last = os.path.getmtime('posted.json')
    hours_gap = (time.time()-last)/3600
    print(f"Hours since last post: {hours_gap}")
    if hours_gap < 5:
        print("SKIP - Posted recently, avoiding Blogger block")
        exit()
except: pass

for job in jobs:
    if is_posted(job['link']): continue
    if is_already_in_blog(job['company'], job['title']):
        save_link(job['link']) # mark as posted to skip next time
        continue
    print(f"Trying: {job['company']} | {job['qual']} | {job['batch']} | {job['loc']}")
    if post_blogger(job):
        url=get_blog_url(job)
        post_telegram(job, url)
        save_link(job['link'])
        print("SUCCESS - Dynamic post done")
        break
    else:
        print("Blocked - will try after 6 hours")
        break
