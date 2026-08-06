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

# === TECH STACK + LOCATIONS YOU WANT ===
TECH_KEYWORDS = ["Java Developer", "Python Developer", "SQL Developer", "Data Analyst", "React Developer", "Web Developer", "Gen AI", "Full Stack", "Backend Developer", "Frontend"]
INDIA_LOCATIONS = ["hyderabad", "bangalore", "bengaluru", "chennai", "pune", "mumbai", "delhi", "india"]

# Duplicate control
SEEN_ROLES = set()

def is_fulltime_tech_job(title, desc, company):
    full = (title + " " + desc + " " + company).lower()

    # 1. INTERNSHIP BAN
    if "internship" in full or " stipend" in full:
        return False

    # 2. FOREIGN WFH BAN - India lekunda remote ante block
    has_india = any(loc in full for loc in INDIA_LOCATIONS)
    if not has_india:
        if "remote" in full or "wfh" in full:
            return False # Foreign remote

    # 3. UK/US BLOCK
    if any(x in full for x in ["united kingdom", "london -", "| uk", "(uk)", "usa only", "us only", "uk only", "(m/f/d)", "dach", "berlin"]):
        return False

    # 4. TECH STACK MUST - Java/Python/SQL/Data Analyst/React/Web/Gen AI/Full Stack okate
    tech_match = any(k.lower() in full for k in TECH_KEYWORDS)
    if not tech_match:
        return False

    # 5. COMPANY ROLE DUPLICATE BAN - Same company same role repeat vaddu
    clean_title = re.sub(r'\|\s*\d+\s*$', '', title).lower()
    role_key = re.sub(r'2026|2025|\(|\)|\|.*', '', clean_title).strip()[:50]
    dup_key = f"{company.lower().strip()}|{role_key}"
    if dup_key in SEEN_ROLES:
        return False
    SEEN_ROLES.add(dup_key)

    return True

def detect_location_simple(title, desc):
    full = (title + " " + desc).lower()
    if "hyderabad" in full or " hyd " in full: return "Hyderabad"
    if "bangalore" in full or "bengaluru" in full: return "Bangalore"
    if "chennai" in full: return "Chennai"
    if "pune" in full: return "Pune"
    if "mumbai" in full: return "Mumbai"
    if "delhi" in full or "noida" in full or "gurgaon" in full: return "Delhi NCR"
    if "vizag" in full: return "Vizag"
    if "vijayawada" in full: return "Vijayawada"
    return "Pan India"

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

def fetch_only_india_no_key():
    jobs = []
    print("[LOG] FINAL - REMOTIVE + ARBEITNOW - HYD/BLR/TECH")

    def safe_json_get(url):
        try:
            r = requests.get(url, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
            if r.status_code!= 200:
                print(f"[LOG] API Status {r.status_code} {url[:50]}")
                return None
            return r.json()
        except Exception as e:
            print(f"[LOG] API Fail {url[:50]} {e}")
            return None

    # === 1. ARBEITNOW API - FREE & NO KEY - INDIA JOBS SUPER ===
    for keyword in ["Python", "Java", "React", "Data Analyst", "SQL"]:
        try:
            url = f"https://www.arbeitnow.com/api/job-board-api?search={keyword}"
            data = safe_json_get(url)
            if not data: continue
            c = 0
            for j in data.get('data', [])[:20]:
                title = j.get('title',''); desc = j.get('description',''); company = j.get('company_name',''); link = j.get('url','')
                # Filter only India / Remote India
                full = (title + " " + desc + " " + company).lower()
                if not any(loc in full for loc in ["india", "hyderabad", "bangalore", "chennai", "pune", "remote"]):
                    continue
                if is_posted(link): continue
                if not is_fulltime_tech_job(title, desc, company):
                    # Relax tech filter for arbeitnow - already keyword search
                    if "intern" in full: continue
                if any(x['link']==link for x in jobs): continue
                qual,batch,exp = parse_dynamic_full(desc, title)
                jt_full, jt_short = detect_job_type(title, desc)
                loc = detect_location_simple(title, desc)
                # Force location if not detected
                if loc == "Pan India" and "hyderabad" in full: loc = "Hyderabad"
                if loc == "Pan India" and "bangalore" in full: loc = "Bangalore"
                jobs.append({"title":title[:90],"company":company or "Company","link":link,"desc":desc,"qual":qual,"batch":batch,"exp":exp,"loc":loc,"job_type_full":jt_full,"job_type_short":jt_short})
                c+=1
            if c>0: print(f"[LOG] Arbeitnow {keyword} Added: {c} | Total: {len(jobs)}")
        except Exception as e:
            print(f"[LOG] Arbeitnow {keyword} fail {e}")

    # === 2. REMOTIVE - INDIA SEARCH ===
    for keyword in TECH_KEYWORDS[:5]:
        data = safe_json_get(f"https://remotive.com/api/remote-jobs?limit=50&search={keyword} India")
        if not data: continue
        c=0
        for j in data.get('jobs', [])[:20]:
            title=j.get('title',''); desc=j.get('description',''); company=j.get('company_name',''); link=j.get('url','')
            if not title: continue
            if is_posted(link): continue
            if not is_fulltime_tech_job(title, desc, company): continue
            if any(x['link']==link for x in jobs): continue
            qual,batch,exp = parse_dynamic_full(desc, title)
            jt_full, jt_short = detect_job_type(title, desc)
            loc = detect_location_simple(title, desc)
            jobs.append({"title":title[:90],"company":company or "Company","link":link,"desc":desc,"qual":qual,"batch":batch,"exp":exp,"loc":loc,"job_type_full":jt_full,"job_type_short":jt_short})
            c+=1
        if c>0: print(f"[LOG] Remotive {keyword} Added: {c} | Total: {len(jobs)}")

    # === 3. FALLBACK - If still 0, relax filter for testing ===
    if len(jobs) == 0:
        print("[LOG] 0 jobs with strict filter - Relaxing for 1 post to keep Adsense active")
        # Take any remote India job from remotive without tech filter
        data = safe_json_get("https://remotive.com/api/remote-jobs?limit=50&search=India")
        if data:
            for j in data.get('jobs', [])[:10]:
                title=j.get('title',''); desc=j.get('description',''); company=j.get('company_name',''); link=j.get('url','')
                if not title or is_posted(link): continue
                if "intern" in (title+desc).lower(): continue
                qual,batch,exp = parse_dynamic_full(desc, title)
                jt_full, jt_short = detect_job_type(title, desc)
                loc = detect_location_simple(title, desc)
                jobs.append({"title":title[:90],"company":company or "Company","link":link,"desc":desc,"qual":qual,"batch":batch,"exp":exp,"loc":loc,"job_type_full":jt_full,"job_type_short":jt_short})

    def sort_key(j):
        if j['loc']=="Hyderabad": return 0
        if j['loc']=="Bangalore": return 1
        if j['loc']=="Chennai": return 2
        if j['loc']=="Pune": return 3
        return 4
    jobs = sorted(jobs, key=sort_key)
    print(f"[LOG] FINAL READY: {len(jobs)} Jobs - {jobs[0]['loc'] if jobs else 'None'} | {jobs[0]['title'][:40] if jobs else ''}")
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
        soup_desc=re.sub(r'\s+',' ',soup_desc).strip()
        neat_desc='. '.join(soup_desc.split('. ')[:4])[:900]
        now=datetime.now().strftime("%d %B %Y")
        html=f"""<div style="font-family:Arial;line-height:1.85;max-width:800px;margin:auto;color:#1e293b;">
<h1 style="font-size:22px;color:#0f172a;">{job['company']} {job['job_type_full']} 2026 | {job['title']} | {job['loc']}</h1>
<p><b>HydHireHub</b> - {job['company']} hiring {job['title']} in <b>{job['loc']}</b>. Tech Stack: Java/Python/SQL/React/Data Analyst.</p>
<table style="width:100%;border-collapse:collapse;margin:18px 0;border:1px solid #e2e8f0;font-size:14px;">
<tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:11px;background:#f8fafc;font-weight:700;width:34%;">Company</td><td style="padding:11px;">{job['company']}</td></tr>
<tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:11px;background:#f8fafc;font-weight:700;">Role</td><td style="padding:11px;"><b>{job['title']}</b></td></tr>
<tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:11px;background:#f8fafc;font-weight:700;">Location</td><td style="padding:11px;"><b>{job['loc']}</b></td></tr>
<tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:11px;background:#f8fafc;font-weight:700;">Qualification</td><td style="padding:11px;">{job['qual']}</td></tr>
<tr><td style="padding:11px;background:#f8fafc;font-weight:700;">Experience</td><td style="padding:11px;">{job['exp']}</td></tr>
</table>
<h3>Job Description</h3><p>{neat_desc}.</p>
<div style="text-align:center;margin:24px 0;"><a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:13px 36px;text-decoration:none;border-radius:6px;font-weight:700;">Apply Now</a></div>
<p style="font-size:11px;color:#94a3b8;">Posted on {now} | HydHireHub | {job['loc']} Jobs</p></div>"""
        msg=MIMEText(html,"html"); msg['Subject']=f"{job['company']} {job['job_type_full']} 2026 | {job['title']} | {job['loc']} | {uid}"; msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
            s.login(YOUR_GMAIL,APP_PASSWORD); s.send_message(msg)
        print(f"[LOG] BLOGGER SENT {job['company']} - {job['loc']} - {job['title'][:30]}")
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
        text=f"{job['company']} {job['job_type_full']} 2026 | {job['title']} | {job['loc']}\n\n💼 {job['title']}\n🏢 {job['company']}\n📍 {job['loc']}\n🎓 {job['qual']}\n\n📄 {url}\n\n#HydHireHub #{job['loc']}Jobs #Java #Python #React"
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",data={"chat_id":CHANNEL_ID,"text":text},timeout=15)
    except: pass

try:
    print("[LOG] ===== HydHireHub TECH + HYD/BLR/CHN/PUNE STARTED =====")
    jobs=fetch_only_india_no_key()
    if len(jobs)<2: print(f"[LOG] Only {len(jobs)} jobs - skip"); exit(0)
    for job in jobs:
        if is_posted(job['link']): continue
        if post_blogger_freshersvoice(job):
            url=get_blog_url(job); post_telegram(job,url); save_link(job['link']); break
    print(f"[LOG] Finished {len(jobs)} jobs")
    exit(0)
except Exception as e:
    print(f"[LOG] MAIN FAIL {e}"); exit(0)
