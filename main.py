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

def parse_dynamic(desc, title):
    text = (title + " " + desc).lower()
    if "mba" in text: qual = "B.E/B.Tech/MBA/MCA/Any Graduate"
    elif "bca" in text or "bsc" in text: qual = "B.E/B.Tech/B.Sc/BCA/MCA"
    else: qual = "B.E/B.Tech/M.Tech/MCA/Any Degree"
    years = re.findall(r'202[0-3]|202[4-6]', text)
    batch = "/".join(sorted(list(set(years)))[:5]) if years else "2023/2024/2025/2026"
    if "2+ years" in text or "3+ years" in text: exp = "Experienced (2+ Years)"
    elif "0-1" in text or "fresher" in text: exp = "Freshers (0-1 Year)"
    else: exp = "0-3 Years (Freshers + Experienced)"
    return qual, batch, exp

def fetch_hyd_only():
    jobs=[]
    print("[LOG] Fetching ONLY Hyderabad jobs...")
    # 1. Jobicy - Filter Hyd only
    try:
        r=requests.get("https://jobicy.com/api/v2/remote-jobs?count=50&geo=india", timeout=20).json()
        all_jobs=r.get('jobs',[])
        print(f"[LOG] Jobicy total: {len(all_jobs)}")
        for j in all_jobs:
            title=j.get('jobTitle',''); desc=j.get('jobDescription',''); company=j.get('companyName','')
            if "hyderabad" not in (title+desc).lower(): continue # HYD ONLY
            if any(x in title.lower() for x in ["für","ä","ö","ß"]): continue
            qual,batch,exp = parse_dynamic(desc, title)
            jobs.append({"title":title[:70],"company":company,"link":j['url'],"desc":desc,"qual":qual,"batch":batch,"exp":exp,"loc":"Hyderabad","source":"Jobicy"})
        print(f"[LOG] Jobicy Hyd only: {len(jobs)}")
    except Exception as e: print(f"Jobicy fail {e}")

    # 2. Remotive - Hyd only
    try:
        r=requests.get("https://remotive.com/api/remote-jobs?limit=100", timeout=20).json()
        c=0
        for j in r['jobs']:
            if "hyderabad" not in (j.get('title','')+j.get('description','')).lower(): continue
            if any(x in j['title'].lower() for x in ["für","ä","ö","ß"]): continue
            qual,batch,exp = parse_dynamic(j['description'], j['title'])
            jobs.append({"title":j['title'][:70],"company":j['company_name'],"link":j['url'],"desc":j['description'],"qual":qual,"batch":batch,"exp":exp,"loc":"Hyderabad","source":"Remotive"})
            c+=1
        print(f"[LOG] Remotive Hyd only: {c} | Total: {len(jobs)}")
    except Exception as e: print(f"Remotive fail {e}")

    # 3. ArbeitNow - Hyd only
    try:
        r=requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=20).json()
        c=0
        for j in r['data']:
            if "hyderabad" not in (j.get('title','')+j.get('description','')).lower(): continue
            qual,batch,exp = parse_dynamic(j.get('description',''), j.get('title',''))
            jobs.append({"title":j.get('title','')[:70],"company":j.get('company_name','Company'),"link":j.get('url',''),"desc":j.get('description',''),"qual":qual,"batch":batch,"exp":exp,"loc":"Hyderabad","source":"ArbeitNow"})
            c+=1
        print(f"[LOG] ArbeitNow Hyd only: {c} | Total: {len(jobs)}")
    except Exception as e: print(f"ArbeitNow fail {e}")

    random.shuffle(jobs)
    print(f"[LOG] TOTAL HYD JOBS READY: {len(jobs)}")
    for j in jobs[:5]: print(f"[LOG] -> {j['company']} | {j['title']} | {j['loc']} | {j['batch']}")
    return jobs

def is_already_in_blog(company, title):
    try:
        r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=30", timeout=15)
        soup=BeautifulSoup(r.text,'xml')
        for item in soup.find_all('item'):
            t=item.title.text.lower()
            if company.split()[0].lower() in t and title.split()[0].lower() in t: return True
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
    uid=random.randint(10000,99999)
    now=datetime.now().strftime("%d %B %Y")
    job['uid']=str(uid)

    # Vinkjobs style blog content
    html=f"""
<div style="font-family:Arial,sans-serif;line-height:1.8;max-width:800px;margin:auto;">
<p>{job['company']} is hiring for the position of {job['title']} Profile. Graduates are eligible to apply for this position. This profile is open for the location of Hyderabad. Complete information about the hiring is mentioned below:</p>

<table border="1" cellpadding="10" cellspacing="0" style="width:100%;border-collapse:collapse;margin:20px 0;">
<tr><td style="background:#f2f2f2;font-weight:bold;">Company Name</td><td><b>{job['company']}</b></td></tr>
<tr><td style="background:#f2f2f2;font-weight:bold;">Profile Hiring for</td><td><b>{job['title']}</b></td></tr>
<tr><td style="background:#f2f2f2;font-weight:bold;">Salary</td><td>As Per Market Standards</td></tr>
<tr><td style="background:#f2f2f2;font-weight:bold;">Work Profile</td><td>Work from Office - Hyderabad</td></tr>
<tr><td style="background:#f2f2f2;font-weight:bold;">Eligibility</td><td>{job['exp']}</td></tr>
<tr><td style="background:#f2f2f2;font-weight:bold;">Location</td><td><b>Hyderabad</b></td></tr>
<tr><td style="background:#f2f2f2;font-weight:bold;">Qualification</td><td>{job['qual']}</td></tr>
<tr><td style="background:#f2f2f2;font-weight:bold;">Batch</td><td>{job['batch']}</td></tr>
<tr><td style="background:#f2f2f2;font-weight:bold;">Job ID</td><td>HH{uid}</td></tr>
</table>

<h3>Eligibility Criteria for {job['company']} Recruitment Drive</h3>
<p>{job['company']} is a global organization delivering innovative solutions. The work you do will directly impact growth. Join us to start <b>Caring. Connecting. Growing together.</b></p>

<p><b>Primary Responsibilities:</b></p>
<ul>
<li>Work on {job['title']} role for Hyderabad location</li>
<li>{job['desc'][:500].replace('<','').replace('>','')}</li>
<li>Collaborate with cross-functional teams to deliver quality results</li>
<li>Increase efficiency and effectiveness of overall operations</li>
<li>Open to work in Hyderabad / Hybrid environment as per guidelines</li>
</ul>

<p><b>Required Qualifications:</b></p>
<ul>
<li>{job['qual']}</li>
<li>Overall {job['exp']} - Relevant experience is added advantage</li>
<li>Good communication and analytical skills</li>
<li>Ability to work independently and share status updates</li>
<li>Batch Eligible: {job['batch']}</li>
</ul>

<h3>How to Apply for {job['company']} Recruitment</h3>
<p>To apply for this job, interested candidates must follow the procedure outlined below:</p>
<p>Click on the "<b>Apply here</b>" button provided below. You will be redirected to the application page.</p>
<ol>
<li>Fill in the application form with all the necessary details.</li>
<li>Submit all relevant documents, if required.</li>
<li>Make sure that all the details entered are correct.</li>
<li>Submit the application form & wait for the company's revert.</li>
</ol>

<div style="text-align:center;margin:30px 0;">
<a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:16px 45px;text-decoration:none;border-radius:8px;font-weight:bold;font-size:18px;">🌐 Apply Here - {job['company']}</a>
</div>

<p><b>IMPORTANT INFORMATION:</b><br>
No fee Charged from candidates / Never pay any amount for getting a job.<br><br>
<b>Many employers prefer Applications on First come First Serve Basis. Apply immediately once the job is posted.</b></p>

<p><i>Posted on {now} | Source: {job['source']} | Location: Hyderabad Only</i></p>
</div>
"""
    msg=MIMEText(html,"html")
    msg['Subject']=f"{job['company']} Hiring {job['title']} - Hyderabad Jobs {uid}"
    msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s: s.login(YOUR_GMAIL, APP_PASSWORD); s.send_message(msg)
        print(f"[LOG] BLOGGER SENT UID:{uid} - {job['company']} - Hyd Only - Vinkjobs style")
        return True
    except Exception as e: print(f"BLOGGER FAIL {e}"); return False

def get_blog_url(job):
    uid=job.get('uid','')
    print(f"[LOG] Searching UID {uid} - wait 10 mins for blog")
    for attempt in range(20):
        time.sleep(30)
        try:
            r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=20", timeout=20)
            soup=BeautifulSoup(r.text,'xml')
            for item in soup.find_all('item'):
                if uid in item.title.text:
                    link=item.find('link').text
                    print(f"[LOG] CORRECT URL FOUND: {link}")
                    return link
        except Exception as e: print(f"RSS fail {e}")
    print("[LOG] UID not found after 10 mins - will use blog homepage search")
    return None

def post_telegram(job, url):
    final_url = url if url else BLOG_URL
    text=f"""🔥 {job['company']} Off Campus Drive 2026

💼 Job Role: {job['title']}
🏢 Company: {job['company']}
🎓 Qualification: {job['qual']}
🔹 Batch: {job['batch']}
🆕 Experience: {job['exp']}
📍 Location: Hyderabad

🌐 Apply Here:
{final_url}

━━━━━━━━━━━━━━━━━━━━
📢 Join Our Telegram Channel
https://t.me/HydHireHub

🌐 Visit Our Blog
https://hydhirehub.blogspot.com
"""
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHANNEL_ID, "text":text})
    print(f"[LOG] TELEGRAM DONE: {final_url}")

jobs=fetch_hyd_only()
if not jobs: print("[LOG] No Hyderabad jobs today - will retry after 6 hours"); exit()
for job in jobs:
    if is_posted(job['link']): continue
    if is_already_in_blog(job['company'], job['title']): save_link(job['link']); continue
    if post_blogger(job):
        url=get_blog_url(job)
        post_telegram(job, url)
        save_link(job['link'])
        print("[LOG] SUCCESS - HYD ONLY - VINKJOBS STYLE")
        break
