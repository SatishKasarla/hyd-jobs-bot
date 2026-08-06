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

TECH_KEYWORDS = ["Java Developer", "Python Developer", "SQL Developer", "Data Analyst", "React Developer", "Web Developer", "Gen AI", "Full Stack", "Backend Developer"]
SEEN_ROLES = set()

def is_fulltime_tech_job(title, desc, company):
    full = (title + " " + desc + " " + company).lower()

    # 1. GERMAN + FAKE + INTERN 100% BLOCK - Adsense violation fix
    if any(x in full for x in ["pflichtpraktikum", "pflicht", "praktikum", "werkstudent", "grafikdesign", "sozial", "elektromeister", "technischer", "dozent", "gmbh", "m/w/d", "m/f/x", "dach", "berlin", "munich", "hamburg", "belo horizonte", "montevideo", "sao paulo", "internship", " stipend"]):
        return False

    # 2. USA/UK ONLY JOBS BLOCK - But India remote ok
    if any(x in full for x in ["united states -", "united kingdom", "london -", "cst timezone", "est timezone", "pst timezone", "united states content reviewer"]):
        return False

    # 3. TECH STACK MUST - Java/Python/SQL/React/Data Analyst/Gen AI/Full Stack
    if not any(k.lower() in full for k in TECH_KEYWORDS):
        return False

    # 4. DUPLICATE BLOCK
    clean_title = re.sub(r'\|\s*\d+\s*$', '', title).lower()
    role_key = re.sub(r'2026|2025|\(|\)|\|.*', '', clean_title).strip()[:50]
    dup_key = f"{company.lower().strip()}|{role_key}"
    if dup_key in SEEN_ROLES:
        return False
    SEEN_ROLES.add(dup_key)
    return True

def detect_location_simple(title, desc):
    full = (title + " " + desc).lower()
    # India locations unte ade - Lekapothe Pan India (WFH) - German kakunda tech job kabatti Pan India ok
    if "hyderabad" in full: return "Hyderabad"
    if "bangalore" in full or "bengaluru" in full: return "Bangalore"
    if "chennai" in full: return "Chennai"
    if "pune" in full: return "Pune"
    if "mumbai" in full: return "Mumbai"
    if "delhi" in full or "noida" in full: return "Delhi NCR"
    # Tech job ayithe India WFH ga treat chey - Fake kadu
    return "Pan India (WFH) - India"

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
    print("[LOG] FINAL - INDIA ONLY - TECH ONLY - NO FAKE")

    def safe_json_get(url):
        try:
            r = requests.get(url, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
            if r.status_code!=200:
                print(f"[LOG] API Status {r.status_code} {url[:50]}")
                return None
            return r.json()
        except Exception as e:
            print(f"[LOG] API Fail {url[:50]} {e}")
            return None

    # 1. ARBEITNOW - STABLE - INDIA FILTER
    for keyword in ["Python", "Java", "React", "Data Analyst", "SQL", "Full Stack"]:
        url = f"https://www.arbeitnow.com/api/job-board-api?search={keyword}"
        data = safe_json_get(url)
        if not data: continue
        c=0
        for j in data.get('data', [])[:25]:
            title=j.get('title',''); desc=j.get('description',''); company=j.get('company_name',''); link=j.get('url','')
            if not title or not link: continue
            if is_posted(link): continue
            if not is_fulltime_tech_job(title, desc, company): continue
            if any(x['link']==link for x in jobs): continue
            qual,batch,exp = parse_dynamic_full(desc, title)
            jt_full, jt_short = detect_job_type(title, desc)
            loc = detect_location_simple(title, desc)
            jobs.append({"title":title[:90],"company":company or "Company","link":link,"desc":desc,"qual":qual,"batch":batch,"exp":exp,"loc":loc,"job_type_full":jt_full,"job_type_short":jt_short})
            c+=1
        if c>0: print(f"[LOG] Arbeitnow {keyword} Added: {c} | Total: {len(jobs)}")

    # 2. REMOTIVE - INDIA ONLY
    for keyword in ["Python India", "Java India", "React India", "Data Analyst India"]:
        data = safe_json_get(f"https://remotive.com/api/remote-jobs?limit=50&search={keyword}")
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
        if c>0: print(f"[LOG] Remotive {keyword} Added: {c}")

    def sort_key(j):
        if j['loc']=="Hyderabad": return 0
        if j['loc']=="Bangalore": return 1
        if j['loc']=="Chennai": return 2
        if j['loc']=="Pune": return 3
        return 4
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
        # HIGH QUALITY CONTENT FOR ADSENSE - 700+ WORDS ORIGINAL
        html=f"""
<div style="font-family:'Segoe UI',Arial;line-height:1.9;max-width:820px;margin:auto;color:#1e293b;">
<h1 style="font-size:24px;color:#0f172a;line-height:1.4;">{job['company']} Recruitment 2026 | {job['title']} | {job['loc']} - Apply Online</h1>
<p style="color:#64748b;font-size:13px;">Updated on {now} | By HydHireHub Team | {job['loc']} Jobs</p>
<p><b>{job['company']}</b> has announced openings for <b>{job['title']}</b> role in <b>{job['loc']}</b>. This opportunity is ideal for candidates with skills in Java, Python, SQL, React, Data Analyst, Gen AI. Complete details below.</p>
<div style="background:#f1f5f9;padding:14px;border-radius:8px;border-left:4px solid #0d6efd;margin:18px 0;"><b>Quick Overview:</b> {job['company']} | {job['title']} | {job['loc']} | {job['qual']} | {job['batch']} | {job['exp']}</div>
<table style="width:100%;border-collapse:collapse;margin:20px 0;border:1px solid #e2e8f0;font-size:14px;">
<tr><td style="padding:12px;background:#f8fafc;font-weight:700;width:35%;border:1px solid #e2e8f0;">Company</td><td style="padding:12px;border:1px solid #e2e8f0;">{job['company']}</td></tr>
<tr><td style="padding:12px;background:#f8fafc;font-weight:700;border:1px solid #e2e8f0;">Role</td><td style="padding:12px;border:1px solid #e2e8f0;"><b>{job['title']}</b></td></tr>
<tr><td style="padding:12px;background:#f8fafc;font-weight:700;border:1px solid #e2e8f0;">Location</td><td style="padding:12px;border:1px solid #e2e8f0;"><b>{job['loc']}</b></td></tr>
<tr><td style="padding:12px;background:#f8fafc;font-weight:700;border:1px solid #e2e8f0;">Qualification</td><td style="padding:12px;border:1px solid #e2e8f0;">{job['qual']}</td></tr>
<tr><td style="padding:12px;background:#f8fafc;font-weight:700;border:1px solid #e2e8f0;">Batch</td><td style="padding:12px;border:1px solid #e2e8f0;">{job['batch']}</td></tr>
<tr><td style="padding:12px;background:#f8fafc;font-weight:700;border:1px solid #e2e8f0;">Experience</td><td style="padding:12px;border:1px solid #e2e8f0;">{job['exp']}</td></tr>
</table>
<h2 style="color:#0f172a;border-left:4px solid #0d6efd;padding-left:12px;">About {job['company']}</h2>
<p>{job['company']} is hiring for {job['title']} in {job['loc']}. Great work culture and growth for Java/Python/React professionals.</p>
<h2 style="color:#0f172a;border-left:4px solid #0d6efd;padding-left:12px;">Job Description</h2>
<p>{soup_desc[:700]}. Working on real projects in {job['title']} domain.</p>
<ul style="margin:10px 0 20px 20px;">
<li>Work on {job['title']} development and implementation</li>
<li>Collaborate with teams in {job['loc']}</li>
<li>Strong knowledge in Java/Python/SQL/React preferred</li>
<li>Problem solving and communication skills</li>
</ul>
<h2 style="color:#0f172a;border-left:4px solid #0d6efd;padding-left:12px;">Eligibility</h2>
<ul style="margin:10px 0 20px 20px;">
<li>Qualification: {job['qual']}</li>
<li>Batch: {job['batch']}</li>
<li>Experience: {job['exp']}</li>
<li>Location: {job['loc']}</li>
</ul>
<h2 style="color:#0f172a;border-left:4px solid #0d6efd;padding-left:12px;">How to Apply?</h2>
<ol style="margin:10px 0 20px 20px;">
<li>Click Apply Now below</li>
<li>Go to official {job['company']} careers page</li>
<li>Read details and Apply</li>
</ol>
<div style="text-align:center;margin:28px 0;"><a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:14px 38px;text-decoration:none;border-radius:8px;font-weight:700;display:inline-block;">Apply Now</a></div>
<div style="background:#fff7ed;padding:14px;border-left:4px solid #f59e0b;font-size:13px;"><b>Disclaimer:</b> HydHireHub not recruitment agency. No fees. Only India jobs - Hyderabad, Bangalore, Chennai, Pune priority. Original content for candidates.</div>
<p style="font-size:11px;color:#94a3b8;margin-top:20px;">Posted on {now} | HydHireHub | {job['loc']} Jobs | Tags: {job['title']}, {job['company']}</p>
</div>
"""
        msg=MIMEText(html,"html"); msg['Subject']=f"{job['company']} {job['job_type_full']} 2026 | {job['title']} | {job['loc']} | {uid}"; msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
            s.login(YOUR_GMAIL,APP_PASSWORD); s.send_message(msg)
        print(f"[LOG] BLOGGER SENT HIGH QUALITY {job['company']} - {job['loc']}")
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
        text=f"{job['company']} {job['job_type_full']} 2026 | {job['title']} | {job['loc']}\n\n💼 {job['title']}\n🏢 {job['company']}\n📍 {job['loc']}\n🎓 {job['qual']}\n\n📄 {url}\n\n#HydHireHub #{job['loc']}Jobs"
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",data={"chat_id":CHANNEL_ID,"text":text},timeout=15)
    except: pass

try:
    print("[LOG] ===== HydHireHub TECH + HYD/BLR/CHN/PUNE - NO FAKE - STARTED =====")
    jobs=fetch_only_india_no_key()
    if len(jobs)<1: print(f"[LOG] Only {len(jobs)} jobs - skip"); exit(0)
    for job in jobs:
        if is_posted(job['link']): continue
        if post_blogger_freshersvoice(job):
            url=get_blog_url(job); post_telegram(job,url); save_link(job['link']); break
    print(f"[LOG] Finished {len(jobs)} jobs - Adsense Safe")
    exit(0)
except Exception as e:
    print(f"[LOG] MAIN FAIL {e}"); exit(0)
