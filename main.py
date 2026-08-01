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

# All India Cities - Only these
INDIA_CITIES = ["hyderabad","bangalore","bengaluru","chennai","pune","vijayawada","vizag","visakhapatnam","mumbai","delhi","noida","gurgaon","gurugram","kolkata","ahmedabad","coimbatore","kochi","indore","jaipur","lucknow","nagpur","secunderabad"]

def detect_job_type(title, desc):
    text = (title + " " + desc).lower()
    if "walk" in text and "in" in text:
        return "Walk-in Drive", "Walk-in", "Walk-in Interview - Direct Interview"
    elif "intern" in text:
        return "Internship", "Internship", "Internship (Stipend Available)"
    elif "off campus" in text or "off-campus" in text:
        return "Off Campus Drive", "Off Campus", "Freshers - Off Campus Hiring"
    elif "fresher" in text and "0" in text:
        return "Off Campus Drive", "Off Campus", "Freshers (0-1 Year) - Off Campus"
    elif "experienced" in text or "2+" in text or "3+" in text:
        return "Recruitment", "Experienced", "Experienced Professionals Hiring"
    else:
        return "Recruitment", "Fresher + Experienced", "0-3 Years - Hiring"

def parse_dynamic_full(desc, title):
    try:
        text = (title + " " + desc).lower()
        # Qualification Dynamic
        if "mba" in text:
            qual = "B.E/B.Tech/MBA/MCA/M.Sc/Any Graduate"
        elif "bca" in text or "bba" in text:
            qual = "B.E/B.Tech/BCA/BBA/B.Sc/MCA"
        elif "diploma" in text:
            qual = "Diploma/B.E/B.Tech/Any Degree"
        else:
            qual = "B.E/B.Tech/M.Tech/MCA/M.Sc/Any Degree"
        # Batch Dynamic
        years = re.findall(r'202[0-9]', text)
        uniq_years = sorted(list(set(years)))
        if uniq_years:
            batch = "/".join(uniq_years[-4:])
        else:
            batch = "2023/2024/2025/2026"
        # Experience Dynamic
        if "0-1" in text or "fresher" in text:
            exp = "Freshers (0-1 Year)"
        elif "1-3" in text or "2+" in text:
            exp = "1-3 Years"
        elif "experienced" in text:
            exp = "Experienced (2+ Years)"
        else:
            exp = "0-3 Years (Freshers & Experienced)"
        return qual, batch, exp
    except:
        return "B.E/B.Tech/MCA/Any Degree","2024/2025/2026","Freshers"

def detect_location(title, desc):
    full = (title + " " + desc).lower()
    for city in INDIA_CITIES:
        if city in full:
            if city == "bengaluru": return "Bangalore"
            if city == "visakhapatnam": return "Vizag"
            return city.capitalize()
    if "pan india" in full or "all india" in full or "india" in full:
        return "Pan India"
    if "remote" in full or "work from home" in full or "wfh" in full:
        return "Remote - Pan India"
    return "Pan India"

def fetch_all_india_dynamic():
    jobs=[]
    print("[LOG] HydHireHub - ALL INDIA - Hyd, Chennai, Bangalore, Pune, Vijayawada, Vizag etc - No Fake")
    blacklist = ["uk only","germany only","europe only","dach","berlin","london","us only","uk citizen","deutschland","für","ä","ö","ß","us citizen","canada only"]

    def is_india_job(title, desc):
        full=(title+" "+desc).lower()
        for bad in blacklist:
            if bad in full: return False
        # Must contain India or Indian city or remote+india context
        if any(c in full for c in INDIA_CITIES) or "india" in full or "pan india" in full:
            return True
        return False

    # 1. Jobicy - India Geo
    try:
        print("[LOG] Fetching Jobicy India...")
        r=requests.get("https://jobicy.com/api/v2/remote-jobs?count=60&geo=india", timeout=30).json()
        count=0
        for j in r.get('jobs',[])[:50]:
            title=j.get('jobTitle',''); desc=j.get('jobDescription',''); company=j.get('companyName','')
            link=j.get('url','')
            if not title or not link: continue
            if not is_india_job(title, desc): continue
            qual,batch,exp = parse_dynamic_full(desc,title)
            job_type_full, job_type_short, exp_text = detect_job_type(title, desc)
            loc = detect_location(title, desc)
            jobs.append({
                "title": title[:90],
                "company": company if company else "Company",
                "link": link,
                "desc": desc,
                "qual": qual,
                "batch": batch,
                "exp": exp_text,
                "loc": loc,
                "job_type_full": job_type_full,
                "job_type_short": job_type_short,
                "source": "Jobicy"
            })
            count+=1
        print(f"[LOG] Jobicy All India Added: {count} | Total: {len(jobs)}")
    except Exception as e: print(f"[LOG] Jobicy fail {e}")

    # 2. Remotive - Filter India
    try:
        print("[LOG] Fetching Remotive...")
        r=requests.get("https://remotive.com/api/remote-jobs?limit=120", timeout=30).json()
        c=0
        for j in r.get('jobs',[])[:100]:
            title=j.get('title',''); desc=j.get('description','')
            if not title: continue
            if not is_india_job(title, desc): continue
            if any(x in title.lower() for x in ["german","dach","berlin","london uk"]): continue
            qual,batch,exp = parse_dynamic_full(desc,title)
            job_type_full, job_type_short, exp_text = detect_job_type(title, desc)
            loc = detect_location(title, desc)
            jobs.append({
                "title": title[:90],
                "company": j.get('company_name','Company'),
                "link": j.get('url',''),
                "desc": desc,
                "qual": qual,
                "batch": batch,
                "exp": exp_text,
                "loc": loc,
                "job_type_full": job_type_full,
                "job_type_short": job_type_short,
                "source": "Remotive"
            })
            c+=1
            if c>=12: break
        print(f"[LOG] Remotive All India Added: {c} | Total: {len(jobs)}")
    except Exception as e: print(f"[LOG] Remotive fail {e}")

    # 3. ArbeitNow - India filter
    try:
        r=requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=20).json()
        c=0
        for j in r.get('data',[])[:50]:
            title=j.get('title',''); desc=j.get('description','')
            if not is_india_job(title, desc): continue
            qual,batch,exp = parse_dynamic_full(desc,title)
            job_type_full, job_type_short, exp_text = detect_job_type(title, desc)
            loc = detect_location(title, desc)
            jobs.append({
                "title": title[:90],
                "company": j.get('company_name','Company'),
                "link": j.get('url',''),
                "desc": desc,
                "qual": qual,
                "batch": batch,
                "exp": exp_text,
                "loc": loc,
                "job_type_full": job_type_full,
                "job_type_short": job_type_short,
                "source": "ArbeitNow"
            })
            c+=1
            if c>=5: break
        print(f"[LOG] ArbeitNow Added: {c} | Total: {len(jobs)}")
    except Exception as e: print(f"[LOG] ArbeitNow fail {e}")

    random.shuffle(jobs)
    print(f"[LOG] FINAL ALL INDIA READY (No Other Countries, No Fake): {len(jobs)}")
    for i,j in enumerate(jobs[:7]):
        print(f"[LOG] {i+1} [{j['job_type_full']}] {j['company']} | {j['loc']} | {j['title'][:50]}")
    return jobs

def is_posted(link):
    try:
        if not os.path.exists('posted.json'): return False
        with open('posted.json','r') as f: return link in json.load(f)
    except: return False

def save_link(link):
    try:
        d=[]
        if os.path.exists('posted.json'):
            with open('posted.json','r') as f: d=json.load(f)
        d.append(link)
        with open('posted.json','w') as f: json.dump(d[-1000:], f)
    except:
        with open('posted.json','w') as f: json.dump([link], f)

def post_blogger_freshersvoice(job):
    try:
        uid=random.randint(10000,99999)
        job['uid']=str(uid)
        clean=BeautifulSoup(job['desc'],'html.parser').get_text()
        clean=re.sub(r'\s+',' ',clean).strip()[:800]
        now=datetime.now().strftime("%d %B %Y")

        # FreshersVoice Format - Dynamic as per job type
        html=f"""
<div style="font-family: 'Segoe UI', Arial, sans-serif; line-height:1.8; max-width:820px; margin:auto; color:#222;">

<p><b>HydHireHub</b> - {job['company']} {job['job_type_full']} 2026 for <b>{job['title']}</b> in {job['loc']}. {job['company']} is hiring {job['job_type_short']} candidates for {job['title']} role. Candidates can apply for this drive from all over India - Hyd, Chennai, Bangalore, Pune, Vijayawada, Vizag and Pan India locations.</p>

<table style="width:100%; border-collapse:collapse; margin:25px 0; border:1px solid #ddd; font-size:15px;">
<tr style="border-bottom:1px solid #ddd;"><td style="padding:14px 16px; background:#f1f5f9; font-weight:bold; width:32%; border-right:1px solid #ddd;">Company Name</td><td style="padding:14px 16px;"><b>{job['company']}</b></td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:14px 16px; background:#f1f5f9; font-weight:bold; border-right:1px solid #ddd;">Job Type</td><td style="padding:14px 16px;"><b>{job['job_type_full']}</b></td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:14px 16px; background:#f1f5f9; font-weight:bold; border-right:1px solid #ddd;">Job Role</td><td style="padding:14px 16px;"><b>{job['title']}</b></td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:14px 16px; background:#f1f5f9; font-weight:bold; border-right:1px solid #ddd;">Job Location</td><td style="padding:14px 16px;"><b>{job['loc']}</b></td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:14px 16px; background:#f1f5f9; font-weight:bold; border-right:1px solid #ddd;">Qualification</td><td style="padding:14px 16px;">{job['qual']}</td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:14px 16px; background:#f1f5f9; font-weight:bold; border-right:1px solid #ddd;">Batch Eligible</td><td style="padding:14px 16px;">{job['batch']}</td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:14px 16px; background:#f1f5f9; font-weight:bold; border-right:1px solid #ddd;">Experience</td><td style="padding:14px 16px;">{job['exp']}</td></tr>
<tr><td style="padding:14px 16px; background:#f1f5f9; font-weight:bold; border-right:1px solid #ddd;">Job ID</td><td style="padding:14px 16px;">HydHireHub{uid}</td></tr>
</table>

<h3 style="color:#0f172a; border-left:4px solid #0d6efd; padding-left:12px;">{job['company']} {job['job_type_full']} 2026 - Job Description</h3>
<p>{clean}</p>

<h3 style="color:#0f172a; border-left:4px solid #0d6efd; padding-left:12px;">Eligibility Criteria for {job['company']} {job['loc']} Jobs</h3>
<ul style="padding-left:20px;">
<li>Qualification: {job['qual']}</li>
<li>Batch: {job['batch']} - All batches from {job['batch']} can apply</li>
<li>Experience: {job['exp']}</li>
<li>Location: {job['loc']} - Candidates from Hyderabad, Chennai, Bangalore, Pune, Vijayawada, Vizag, Pan India can apply</li>
<li>Good communication and analytical skills</li>
</ul>

<h3 style="color:#0f172a; border-left:4px solid #0d6efd; padding-left:12px;">How to Apply for {job['company']} {job['job_type_full']} 2026</h3>
<ol style="padding-left:20px;">
<li>Click on Apply Here button below</li>
<li>You will be redirected to official application page</li>
<li>Fill details and upload resume</li>
<li>Submit and wait for interview call</li>
</ol>

<div style="text-align:center; margin:35px 0;">
<a href="{job['link']}" style="background:#0d6efd; color:#fff; padding:16px 50px; text-decoration:none; border-radius:8px; font-weight:bold; font-size:18px; display:inline-block;">🌐 Apply Here - {job['company']}</a>
</div>

<div style="background:#fef9c3; padding:14px; border-radius:8px; border-left:4px solid #eab308;">
<b>Note:</b> No fee charged - HydHireHub never asks for money. This is {job['job_type_full']} - {job['loc']} - Direct company apply link only. No fake links.
</div>

<p style="font-size:13px; color:#64748b; margin-top:25px;">Posted on {now} | HydHireHub | {job['job_type_full']} | {job['loc']} Jobs | Source: {job['source']} | Fresher Jobs 2026 | Work From Home | Off Campus Drive | Walk-in Drive | Pan India Jobs</p>

</div>
"""
        msg=MIMEText(html,"html")
        # SEO Title - FreshersVoice Style - Dynamic
        msg['Subject']=f"HydHireHub | {job['company']} {job['job_type_full']} 2026 | {job['title']} | {job['loc']} | Fresher Jobs | {uid}"
        msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s: s.login(YOUR_GMAIL, APP_PASSWORD); s.send_message(msg)
        print(f"[LOG] BLOGGER SENT [{job['job_type_full']}] UID:{uid} - {job['company']} - {job['loc']} - FreshersVoice Format")
        return True
    except Exception as e: print(f"[LOG] BLOGGER FAIL {e}"); return False

def get_blog_url(job):
    uid=job.get('uid','')
    for _ in range(8):
        time.sleep(20)
        try:
            r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=15", timeout=15)
            soup=BeautifulSoup(r.text,'xml')
            for item in soup.find_all('item'):
                if uid in item.title.text: return item.find('link').text
        except: pass
    return BLOG_URL

def post_telegram(job, url):
    try:
        text=f"""🔥 HydHireHub | {job['company']} {job['job_type_full']}

💼 Role: {job['title']}
🏢 Company: {job['company']}
📍 Location: {job['loc']}
🎓 Qualification: {job['qual']}
🔹 Batch: {job['batch']}
💼 Type: {job['job_type_full']}

🌐 Apply:
{url}

━━━━━━━━━━━━
https://t.me/HydHireHub
All India Jobs - Hyd | Chennai | Bangalore | Pune | Vijayawada | Vizag
"""
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHANNEL_ID,"text":text}, timeout=15)
        print(f"[LOG] TELEGRAM DONE [{job['job_type_full']}] - {job['loc']}")
    except Exception as e: print(f"Telegram fail {e}")

# MAIN
try:
    print("[LOG] ===== HydHireHub All India Bot Started - FreshersVoice Dynamic Format =====")
    jobs=fetch_all_india_dynamic()
    print(f"[LOG] Total Jobs: {len(jobs)}")
    if not jobs: print("[LOG] No India jobs today"); exit(0)
    for job in jobs:
        if is_posted(job['link']): continue
        if post_blogger_freshersvoice(job):
            url=get_blog_url(job)
            post_telegram(job, url)
            save_link(job['link'])
            print(f"[LOG] SUCCESS - {job['job_type_full']} - {job['loc']} - {job['company']}")
            break
    print("[LOG] ===== Bot Finished OK - No Fake Links - All India HydHireHub =====")
    exit(0)
except Exception as e:
    print(f"[LOG] MAIN FAIL {e}")
    exit(0)
