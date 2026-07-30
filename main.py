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
    print("[LOG] Fetching ONLY India/Hyderabad jobs - UK/Germany/US block...")

    blacklist = ["uk only", "germany only", "europe only", "eu only", "us only", "usa only", "united kingdom", "deutschland", "berlin", "london", "dach", "european", "us citizen", "uk citizen"]
    
    def is_valid_job(title, desc):
        full = (title + " " + desc).lower()
        # Blacklist check - UK/Germany/US only jobs block
        for bad in blacklist:
            if bad in full and "india" not in full and "hyderabad" not in full:
                return False, "blocked"
        # Must have India or Hyderabad or Asia
        if "hyderabad" in full:
            return True, "Hyderabad"
        if "india" in full or "hyderabad eligible" in full or ("remote" in full and "asia" in full):
            return True, "Remote - Hyderabad Eligible"
        if "remote" in full and ("india" in full or "hyderabad" in full):
            return True, "Remote - Hyderabad Eligible"
        # Pure remote with no location but we allow only if from India API
        if "india" in full:
            return True, "Remote - Hyderabad Eligible"
        return False, "no"

    # 1. Jobicy - India geo so mostly India only - but still filter
    try:
        r=requests.get("https://jobicy.com/api/v2/remote-jobs?count=50&geo=india", timeout=20).json()
        all_jobs=r.get('jobs',[])
        print(f"[LOG] Jobicy total India: {len(all_jobs)}")
        for j in all_jobs:
            title=j.get('jobTitle',''); desc=j.get('jobDescription',''); company=j.get('companyName','')
            if any(x in title.lower() for x in ["für","ä","ö","ß","dach"]): continue
            valid, loc = is_valid_job(title, desc)
            if not valid: continue
            qual,batch,exp = parse_dynamic(desc, title)
            jobs.append({"title":title[:70],"company":company,"link":j['url'],"desc":desc,"qual":qual,"batch":batch,"exp":exp,"loc":loc,"source":"Jobicy"})
        print(f"[LOG] Jobicy Hyd + Eligible after block: {len(jobs)}")
    except Exception as e: print(f"Jobicy fail {e}")

    # 2. Remotive - strict filter
    try:
        r=requests.get("https://remotive.com/api/remote-jobs?limit=100", timeout=20).json()
        c=0
        for j in r['jobs']:
            title=j.get('title',''); desc=j.get('description','')
            if any(x in title.lower() for x in ["für","ä","ö","ß","dach","german"]): continue
            if "senior sales manager dach" in title.lower(): continue # Block that UK/Germany job
            valid, loc = is_valid_job(title, desc)
            if not valid: continue
            qual,batch,exp = parse_dynamic(desc, title)
            jobs.append({"title":title[:70],"company":j['company_name'],"link":j['url'],"desc":desc,"qual":qual,"batch":batch,"exp":exp,"loc":loc,"source":"Remotive"})
            c+=1
            if c>=5: break
        print(f"[LOG] Remotive Hyd + Eligible after block: {c} | Total: {len(jobs)}")
    except Exception as e: print(f"Remotive fail {e}")

    # 3. ArbeitNow - Hyd + India only
    try:
        r=requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=20).json()
        c=0
        for j in r['data'][:40]:
            title=j.get('title',''); desc=j.get('description','')
            full=(title+desc).lower()
            if "hyderabad" not in full and "india" not in full: continue # ONLY India/Hyd
            if any(x in full for x in ["uk only", "germany", "berlin", "london"]): continue
            valid, loc = is_valid_job(title, desc)
            if not valid: continue
            qual,batch,exp = parse_dynamic(desc, title)
            jobs.append({"title":title[:70],"company":j.get('company_name','Company'),"link":j.get('url',''),"desc":desc,"qual":qual,"batch":batch,"exp":exp,"loc":loc,"source":"ArbeitNow"})
            c+=1
            if c>=4: break
        print(f"[LOG] ArbeitNow after block: {c} | Total: {len(jobs)}")
    except Exception as e: print(f"ArbeitNow fail {e}")

    random.shuffle(jobs)
    print(f"[LOG] TOTAL FINAL HYD ONLY READY (UK/DE/US BLOCKED): {len(jobs)}")
    for j in jobs[:5]: print(f"[LOG] -> {j['company']} | {j['loc']} | {j['title'][:40]}")
    return jobs

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

    # HTML tags motham clean - No <div> leak
    clean_desc = BeautifulSoup(job['desc'], 'html.parser').get_text()
    clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()[:600] # only 600 chars clean text

    # Off Campus dynamic - Fresher ayithe Off Campus, Experienced ayithe Hiring
    if "Fresher" in job['exp']:
        drive_type = "Off Campus Drive"
        hiring_text = f"{job['company']} Off Campus Drive for {job['title']}"
    else:
        drive_type = "Hiring / Recruitment"
        hiring_text = f"{job['company']} is Hiring for {job['title']}"

    html=f"""
<div style="font-family:Arial,sans-serif;line-height:1.9;max-width:800px;margin:auto;color:#222;">
<p>{hiring_text} in Hyderabad. {job['company']} is hiring for the position of {job['title']} Profile. Graduates are eligible to apply for this position. Complete information about the hiring is mentioned below:</p>

<table style="width:100%;border-collapse:collapse;margin:25px 0;border:1px solid #ddd;font-size:15px;">
<tr style="border-bottom:1px solid #ddd;"><td style="padding:12px 15px;background:#f8f9fa;font-weight:bold;width:35%;border-right:1px solid #ddd;">Company Name</td><td style="padding:12px 15px;"><b>{job['company']}</b></td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:12px 15px;background:#f8f9fa;font-weight:bold;border-right:1px solid #ddd;">Profile Hiring for</td><td style="padding:12px 15px;"><b>{job['title']}</b></td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:12px 15px;background:#f8f9fa;font-weight:bold;border-right:1px solid #ddd;">Salary</td><td style="padding:12px 15px;">As Per Market Standards</td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:12px 15px;background:#f8f9fa;font-weight:bold;border-right:1px solid #ddd;">Work Profile</td><td style="padding:12px 15px;">Work from Office - Hyderabad</td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:12px 15px;background:#f8f9fa;font-weight:bold;border-right:1px solid #ddd;">Eligibility</td><td style="padding:12px 15px;">{job['exp']}</td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:12px 15px;background:#f8f9fa;font-weight:bold;border-right:1px solid #ddd;">Location</td><td style="padding:12px 15px;"><b>Hyderabad</b></td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:12px 15px;background:#f8f9fa;font-weight:bold;border-right:1px solid #ddd;">Qualification</td><td style="padding:12px 15px;">{job['qual']}</td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:12px 15px;background:#f8f9fa;font-weight:bold;border-right:1px solid #ddd;">Batch</td><td style="padding:12px 15px;">{job['batch']}</td></tr>
<tr><td style="padding:12px 15px;background:#f8f9fa;font-weight:bold;border-right:1px solid #ddd;">Job ID</td><td style="padding:12px 15px;">HH{uid}</td></tr>
</table>

<h3 style="margin-top:30px;color:#0d2a54;">Eligibility Criteria for {job['company']} {drive_type}</h3>
<p>{job['company']} is a leading company delivering innovative solutions for clients worldwide. Be part of a dynamic team where your work directly impacts growth. Join us to start <b>Caring. Connecting. Growing together.</b></p>

<p><b>Primary Responsibilities:</b></p>
<ul style="padding-left:20px;">
<li>Work on {job['title']} role for Hyderabad location</li>
<li>{clean_desc}</li>
<li>Collaborate with cross-functional teams to deliver quality results</li>
<li>Increase efficiency and effectiveness of overall operations</li>
<li>Open to work in Hyderabad / Hybrid environment as per company guidelines</li>
</ul>

<p><b>Required Qualifications:</b></p>
<ul style="padding-left:20px;">
<li>{job['qual']} from recognized university</li>
<li>Eligibility: {job['exp']} - Relevant experience is added advantage</li>
<li>Good communication and analytical skills</li>
<li>Ability to work independently and share status updates</li>
<li>Batch Eligible: {job['batch']}</li>
</ul>

<h3 style="margin-top:30px;color:#0d2a54;">How to Apply for {job['company']} Recruitment</h3>
<p>To apply for this job, interested candidates must follow the procedure outlined below:</p>
<ol style="padding-left:20px;">
<li>Click on the "<b>Apply here</b>" button provided below. You will be redirected to the application page.</li>
<li>Fill in the application form with all the necessary details.</li>
<li>Submit all relevant documents, if required.</li>
<li>Make sure that all the details entered are correct.</li>
<li>Submit the application form & wait for the company's revert.</li>
</ol>

<div style="text-align:center;margin:35px 0;">
<a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:16px 45px;text-decoration:none;border-radius:8px;font-weight:bold;font-size:18px;display:inline-block;">🌐 Apply Here - {job['company']}</a>
</div>

<p style="background:#fff3cd;padding:12px;border-radius:6px;"><b>IMPORTANT INFORMATION:</b><br>
No fee Charged from candidates / Never pay any amount for getting a job.<br>
<b>Many employers prefer Applications on First come First Serve Basis. Apply immediately once the job is posted.</b></p>

<p style="font-size:13px;color:#666;"><i>Posted on {now} | Source: {job['source']} | {drive_type} | Location: Hyderabad Only</i></p>
</div>
"""
    msg=MIMEText(html,"html")
    msg['Subject']=f"{job['company']} {drive_type} {job['title']} - Hyderabad Jobs {uid}"
    msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s: s.login(YOUR_GMAIL, APP_PASSWORD); s.send_message(msg)
        print(f"[LOG] BLOGGER SENT UID:{uid} - {job['company']} - {drive_type} - Clean HTML")
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
