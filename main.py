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
ADZUNA_APP_ID = os.environ.get("ADZUNA_ID")
ADZUNA_APP_KEY = os.environ.get("ADZUNA_KEY")

TECH_KEYWORDS = ["Java Developer", "Python Developer", "SQL Developer", "Data Analyst", "React Developer", "Web Developer", "Gen AI", "Full Stack", "Backend Developer"]
SEEN_ROLES = set()

def is_fulltime_tech_job(title, desc, company):
    full = (title + " " + desc + " " + company).lower()
    if any(x in full for x in ["pflichtpraktikum", "praktikum", "werkstudent", "grafikdesign", "sozial", "elektromeister", "technischer", "dozent", "gmbh", "m/w/d", "m/f/x", "dach", "berlin", "munich", "hamburg", "belo horizonte", "montevideo", "sao paulo", "internship", " stipend"]):
        return False
    if any(x in full for x in ["united states -", "united kingdom", "london -", "cst timezone", "est timezone", "pst timezone", "united states content reviewer"]):
        return False
    if not any(k.lower() in full for k in TECH_KEYWORDS):
        return False
    clean_title = re.sub(r'\|\s*\d+\s*$', '', title).lower()
    role_key = re.sub(r'2026|2025|\(|\)|\|.*', '', clean_title).strip()[:50]
    dup_key = f"{company.lower().strip()}|{role_key}"
    if dup_key in SEEN_ROLES:
        return False
    SEEN_ROLES.add(dup_key)
    return True

def detect_location_simple(title, desc):
    full = (title + " " + desc).lower()
    if "hyderabad" in full: return "Hyderabad"
    if "bangalore" in full or "bengaluru" in full: return "Bangalore"
    if "chennai" in full: return "Chennai"
    if "pune" in full: return "Pune"
    if "mumbai" in full: return "Mumbai"
    if "delhi" in full or "noida" in full or "gurgaon" in full: return "Delhi NCR"
    return "Hyderabad" # Default Hyderabad for India jobs

def parse_dynamic_full(desc, title):
    text = (title + " " + desc).lower()
    qual = "B.E/B.Tech/MCA/Any Degree"
    if "mba" in text: qual = "B.E/B.Tech/MBA/MCA/Any Graduate"
    years = re.findall(r'202[4-6]', text)
    batch = "/".join(sorted(set(years))[:3]) if years else "2024/2025/2026"
    exp = "0-3 Years"
    if "0-1" in text or "fresher" in text: exp = "Freshers (0-1 Year)"
    return qual, batch, exp

def detect_job_type(title, desc):
    text = (title + " " + desc).lower()
    if "walk" in text and "in" in text: return "Walk-in Drive", "Walk-in"
    if "off campus" in text: return "Off Campus Drive", "Off Campus"
    if "fresher" in text: return "Off Campus Drive", "Off Campus"
    return "Recruitment", "Fresher + Experienced"

def safe_json_get(url, headers=None):
    try:
        r = requests.get(url, timeout=30, headers=headers or {"User-Agent":"Mozilla/5.0"})
        if r.status_code!=200:
            print(f"[LOG] API Status {r.status_code} {url[:80]}")
            return None
        return r.json()
    except Exception as e:
        print(f"[LOG] API Fail {url[:80]} {e}")
        return None

def fetch_only_india_no_key():
    jobs = []
    print("[LOG] START - NEXPRO247 STYLE - HYD/BLR/LOCAL")

    # 1. ADZUNA INDIA - 100% Local Jobs (Best for Nexpro247 clone)
    if ADZUNA_APP_ID and ADZUNA_APP_KEY:
        for city in ["Hyderabad", "Bangalore", "Chennai", "Pune"]:
            for keyword in ["Data Analyst", "Python Developer", "Java Developer", "SQL Developer"]:
                url = f"https://api.adzuna.com/v1/api/jobs/in/search/1?app_id={ADZUNA_APP_ID}&app_key={ADZUNA_APP_KEY}&results_per_page=15&what={keyword}&where={city}&content-type=application/json"
                data = safe_json_get(url)
                if not data: continue
                c=0
                for j in data.get('results', []):
                    title=j.get('title',''); desc=j.get('description',''); company=j.get('company',{}).get('display_name','') or "Top Company"; link=j.get('redirect_url','')
                    if not title or not link: continue
                    if is_posted(link): continue
                    if any(x['link']==link for x in jobs): continue
                    # Adzuna data is already India filtered
                    qual,batch,exp = parse_dynamic_full(desc, title)
                    jt_full, jt_short = detect_job_type(title, desc)
                    jobs.append({"title":title[:90],"company":company,"link":link,"desc":desc,"qual":qual,"batch":batch,"exp":exp,"loc":city,"job_type_full":jt_full,"job_type_short":jt_short})
                    c+=1
                if c>0: print(f"[LOG] Adzuna {keyword} in {city} Added: {c}")
    else:
        print("[LOG] ADZUNA_ID/KEY not set - Skipping Adzuna (Add secrets for local jobs)")

    # 2. ARBEITNOW - Filtered for India/Hyderabad only
    for keyword in ["Python India", "Java India Hyderabad", "Data Analyst India", "React India"]:
        url = f"https://www.arbeitnow.com/api/job-board-api?search={keyword}"
        data = safe_json_get(url)
        if not data: continue
        c=0
        for j in data.get('data', [])[:20]:
            title=j.get('title',''); desc=j.get('description',''); company=j.get('company_name',''); link=j.get('url','')
            if not title or not link: continue
            if is_posted(link): continue
            # Force India check
            if "india" not in (title+" "+desc+company).lower() and "hyderabad" not in (title+" "+desc).lower() and "bangalore" not in (title+" "+desc).lower():
                continue
            if not is_fulltime_tech_job(title, desc, company): continue
            if any(x['link']==link for x in jobs): continue
            qual,batch,exp = parse_dynamic_full(desc, title)
            jt_full, jt_short = detect_job_type(title, desc)
            loc = detect_location_simple(title, desc)
            jobs.append({"title":title[:90],"company":company or "Company","link":link,"desc":desc,"qual":qual,"batch":batch,"exp":exp,"loc":loc,"job_type_full":jt_full,"job_type_short":jt_short})
            c+=1
        if c>0: print(f"[LOG] Arbeitnow {keyword} Added: {c} | Total: {len(jobs)}")

    def sort_key(j):
        order = {"Hyderabad":0, "Bangalore":1, "Chennai":2, "Pune":3, "Mumbai":4}
        return order.get(j['loc'], 5)
    jobs = sorted(jobs, key=sort_key)
    print(f"[LOG] FINAL READY: {len(jobs)} Jobs")
    for i, j in enumerate(jobs[:5]):
        print(f"[LOG] {i+1} {j['company']} | {j['loc']} | {j['title'][:45]}")
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
        with open('posted.json','w') as f: json.dump(d[-1000:],f)
    except:
        with open('posted.json','w') as f: json.dump([link],f)

def post_blogger_freshersvoice(job):
    try:
        uid=random.randint(10000,99999); job['uid']=str(uid)
        soup_desc=BeautifulSoup(job['desc'],'html.parser').get_text()
        soup_desc=re.sub(r'\s+',' ',soup_desc).strip()[:1500]
        now=datetime.now().strftime("%d %B %Y")
        html=f"""
<div style="font-family:'Segoe UI',Arial;line-height:1.9;max-width:820px;margin:auto;color:#1e293b;">
<h1 style="font-size:24px;color:#0f172a;line-height:1.4;">{job['company']} Recruitment 2026 | {job['title']} | {job['loc']} - Apply Online</h1>
<p style="color:#64748b;font-size:13px;">Updated on {now} | By HydHireHub Team | {job['loc']} Jobs</p>
<p><b>{job['company']}</b> has announced openings for <b>{job['title']}</b> role in <b>{job['loc']}</b>. Complete details below.</p>
<div style="background:#f1f5f9;padding:14px;border-radius:8px;border-left:4px solid #0d6efd;margin:18px 0;"><b>Quick Overview:</b> {job['company']} | {job['title']} | {job['loc']} | {job['qual']} | {job['batch']} | {job['exp']}</div>
<table style="width:100%;border-collapse:collapse;margin:20px 0;border:1px solid #e2e8f0;font-size:14px;">
<tr><td style="padding:12px;background:#f8fafc;font-weight:700;width:35%;border:1px solid #e2e8f0;">Company</td><td style="padding:12px;border:1px solid #e2e8f0;">{job['company']}</td></tr>
<tr><td style="padding:12px;background:#f8fafc;font-weight:700;border:1px solid #e2e8f0;">Role</td><td style="padding:12px;border:1px solid #e2e8f0;"><b>{job['title']}</b></td></tr>
<tr><td style="padding:12px;background:#f8fafc;font-weight:700;border:1px solid #e2e8f0;">Location</td><td style="padding:12px;border:1px solid #e2e8f0;"><b>{job['loc']}</b></td></tr>
<tr><td style="padding:12px;background:#f8fafc;font-weight:700;border:1px solid #e2e8f0;">Qualification</td><td style="padding:12px;border:1px solid #e2e8f0;">{job['qual']}</td></tr>
<tr><td style="padding:12px;background:#f8fafc;font-weight:700;border:1px solid #e2e8f0;">Batch</td><td style="padding:12px;border:1px solid #e2e8f0;">{job['batch']}</td></tr>
<tr><td style="padding:12px;background:#f8fafc;font-weight:700;border:1px solid #e2e8f0;">Experience</td><td style="padding:12px;border:1px solid #e2e8f0;">{job['exp']}</td></tr>
</table>
<h2 style="color:#0f172a;border-left:4px solid #0d6efd;padding-left:12px;">Job Description</h2>
<p>{soup_desc[:700]}. Working on real projects in {job['title']} domain at {job['loc']}.</p>
<h2 style="color:#0f172a;border-left:4px solid #0d6efd;padding-left:12px;">How to Apply?</h2>
<ol style="margin:10px 0 20px 20px;"><li>Click Apply Now below</li><li>Go to official {job['company']} careers page</li><li>Apply for {job['loc']} location</li></ol>
<div style="text-align:center;margin:28px 0;"><a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:14px 38px;text-decoration:none;border-radius:8px;font-weight:700;display:inline-block;">Apply Now - {job['loc']}</a></div>
<div style="background:#fff7ed;padding:14px;border-left:4px solid #f59e0b;font-size:13px;"><b>Disclaimer:</b> HydHireHub - {job['loc']} Jobs Only. No fees.</div>
</div>
"""
        msg=MIMEText(html,"html"); msg['Subject']=f"{job['company']} {job['job_type_full']} 2026 | {job['title']} | {job['loc']} | {uid}"; msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
            s.login(YOUR_GMAIL,APP_PASSWORD); s.send_message(msg)
        print(f"[LOG] BLOGGER SENT {job['company']} - {job['loc']}")
        return True
    except Exception as e:
        print(f"[LOG] BLOGGER FAIL {e}"); return False

def get_blog_url(job):
    uid=job.get('uid',''); time.sleep(30)
    for attempt in range(6):
        try:
            r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=20",timeout=20)
            soup=BeautifulSoup(r.text,'xml'); items=soup.find_all('item')
            for item in items:
                if uid in (item.find('title').text if item.find('title') else ""):
                    link=item.find('link').text; print(f"[LOG] BLOG URL FOUND: {link}"); return link
            if attempt>=2 and items:
                return items[0].find('link').text
        except: pass
        time.sleep(15)
    return BLOG_URL

def post_telegram(job,url):
    try:
        text=f"{job['company']} {job['job_type_full']} 2026 | {job['title']} | {job['loc']}\n\n💼 {job['title']}\n🏢 {job['company']}\n📍 {job['loc']}\n🎓 {job['qual']}\n\n📄 {url}\n\n#HydHireHub #{job['loc']}Jobs #HyderabadJobs"
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",data={"chat_id":CHANNEL_ID,"text":text},timeout=15)
    except: pass

try:
    print("[LOG] ===== HydHireHub NEXPRO STYLE - LOCAL JOBS STARTED =====")
    jobs=fetch_only_india_no_key()
    if len(jobs)<1: print(f"[LOG] Only {len(jobs)} jobs - skip"); exit(0)
    for job in jobs:
        if is_posted(job['link']): continue
        if post_blogger_freshersvoice(job):
            url=get_blog_url(job); post_telegram(job,url); save_link(job['link']); break
    print(f"[LOG] Finished {len(jobs)} jobs")
    exit(0)
except Exception as e:
    print(f"[LOG] MAIN FAIL {e}"); exit(0)
