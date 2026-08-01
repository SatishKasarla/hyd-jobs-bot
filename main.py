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

def detect_job_type(title, desc):
    text = (title + " " + desc).lower()
    if "walk" in text and "in" in text:
        return "Walk-in Drive", "Walk-in", "Walk-in Interview"
    elif "intern" in text:
        return "Internship", "Internship", "Internship"
    elif "off campus" in text:
        return "Off Campus Drive", "Off Campus", "Freshers Off Campus"
    elif "fresher" in text:
        return "Off Campus Drive", "Off Campus", "Freshers"
    else:
        return "Recruitment", "Fresher + Experienced", "0-3 Years Hiring"

def parse_dynamic_full(desc, title):
    text = (title + " " + desc).lower()
    qual = "B.E/B.Tech/MCA/Any Degree"
    if "mba" in text:
        qual = "B.E/B.Tech/MBA/MCA/Any Graduate"
    years = re.findall(r'202[4-6]', text)
    batch = "/".join(sorted(set(years))[:3]) if years else "2024/2025/2026"
    exp = "0-3 Years"
    if "0-1" in text:
        exp = "Freshers (0-1 Year)"
    return qual, batch, exp

def detect_location_simple(title, desc):
    full = (title + " " + desc).lower()
    if "hyderabad" in full:
        return "Hyderabad"
    if "bangalore" in full or "bengaluru" in full:
        return "Bangalore"
    if "chennai" in full:
        return "Chennai"
    if "pune" in full:
        return "Pune"
    if "vijayawada" in full:
        return "Vijayawada"
    if "vizag" in full or "visakhapatnam" in full:
        return "Vizag"
    if "mumbai" in full:
        return "Mumbai"
    if "delhi" in full or "noida" in full:
        return "Delhi NCR"
    return "Pan India (WFH/Remote)"

def fetch_only_india_no_key():
    jobs = []
    print("[LOG] HydHireHub - ONLY INDIA - NO (m/f/d)")
    blacklist = ["uk only", "germany only", "dach only", "berlin only", "london uk", "für", "ä", "ö", "ß", "canada only", "(m/f/d)", "(f/m/d)", "(m/w/d)", "(w/m/d)", "m/f/d", "m/w/d"]

    def is_allowed(title, desc):
        full = (title + " " + desc).lower()
        for b in blacklist:
            if b in full:
                return False
        # Block German jobs
        if "(m/f/d)" in title or "(m/w/d)" in title:
            return False
        if "westwing" in title.lower() and "m/f/d" in title.lower():
            return False
        return True

    try:
        print("[LOG] Fetching Jobicy India...")
        r = requests.get("https://jobicy.com/api/v2/remote-jobs?count=50&geo=india", timeout=30).json()
        c = 0
        for j in r.get('jobs', [])[:40]:
            title = j.get('jobTitle', '')
            desc = j.get('jobDescription', '')
            company = j.get('companyName', '')
            link = j.get('url', '')
            if not title or not link:
                continue
            if not is_allowed(title, desc):
                continue
            qual, batch, exp = parse_dynamic_full(desc, title)
            jt_full, jt_short, exp_text = detect_job_type(title, desc)
            loc = detect_location_simple(title, desc)
            jobs.append({"title": title[:90], "company": company or "Company", "link": link, "desc": desc, "qual": qual, "batch": batch, "exp": exp_text, "loc": loc, "job_type_full": jt_full, "job_type_short": jt_short, "source": "Jobicy India"})
            c += 1
        print(f"[LOG] Jobicy India Added: {c} | Total: {len(jobs)}")
    except Exception as e:
        print(f"[LOG] Jobicy fail {e}")

    try:
        print("[LOG] Fetching Remotive...")
        r = requests.get("https://remotive.com/api/remote-jobs?limit=50", timeout=30).json()
        c = 0
        for j in r.get('jobs', [])[:40]:
            title = j.get('title', '')
            desc = j.get('description', '')
            if not title:
                continue
            if not is_allowed(title, desc):
                continue
            # Block SpaceX, etc - US only companies not hiring India
            if any(x in title.lower() for x in ["spacex", "starlink", "tesla"]):
                continue
            qual, batch, exp = parse_dynamic_full(desc, title)
            jt_full, jt_short, exp_text = detect_job_type(title, desc)
            loc = detect_location_simple(title, desc)
            jobs.append({"title": title[:90], "company": j.get('company_name', 'Company'), "link": j.get('url', ''), "desc": desc, "qual": qual, "batch": batch, "exp": exp_text, "loc": loc, "job_type_full": jt_full, "job_type_short": jt_short, "source": "Remotive India"})
            c += 1
            if c >= 10:
                break
        print(f"[LOG] Remotive Added: {c} | Total: {len(jobs)}")
    except Exception as e:
        print(f"[LOG] Remotive fail {e}")

    try:
        print("[LOG] Fetching ArbeitNow...")
        r = requests.get("https://www.arbeitnow.com/api/job-board-api?search=remote", timeout=25).json()
        c = 0
        for j in r.get('data', [])[:40]:
            title = j.get('title', '')
            desc = j.get('description', '')
            if not title:
                continue
            if not is_allowed(title, desc):
                continue
            qual, batch, exp = parse_dynamic_full(desc, title)
            jt_full, jt_short, exp_text = detect_job_type(title, desc)
            loc = detect_location_simple(title, desc)
            jobs.append({"title": title[:90], "company": j.get('company_name', 'Company'), "link": j.get('url', ''), "desc": desc, "qual": qual, "batch": batch, "exp": exp_text, "loc": loc, "job_type_full": jt_full, "job_type_short": jt_short, "source": "ArbeitNow"})
            c += 1
            if c >= 8:
                break
        print(f"[LOG] ArbeitNow Added: {c} | Total: {len(jobs)}")
    except Exception as e:
        print(f"[LOG] ArbeitNow fail {e}")

    try:
        print("[LOG] Fetching TheMuse...")
        r = requests.get("https://www.themuse.com/api/public/jobs?category=Software%20Engineering&page=0", timeout=20).json()
        c = 0
        for j in r.get('results', [])[:20]:
            title = j.get('name', '')
            company = j.get('company', {}).get('name', 'Company')
            link = j.get('refs', {}).get('landing_page', '')
            desc = j.get('contents', '')
            if not title or not link:
                continue
            if not is_allowed(title, desc):
                continue
            if "spacex" in company.lower() or "uber" in company.lower():
                continue
            qual, batch, exp = parse_dynamic_full(desc, title)
            jt_full, jt_short, exp_text = detect_job_type(title, desc)
            loc = "Pan India (Remote)"
            jobs.append({"title": title[:90], "company": company, "link": link, "desc": desc, "qual": qual, "batch": batch, "exp": exp_text, "loc": loc, "job_type_full": jt_full, "job_type_short": jt_short, "source": "TheMuse India"})
            c += 1
            if c >= 4:
                break
        print(f"[LOG] TheMuse Added: {c} | Total: {len(jobs)}")
    except Exception as e:
        print(f"[LOG] TheMuse fail {e}")

    random.shuffle(jobs)
    print(f"[LOG] FINAL ONLY INDIA NO (m/f/d) READY: {len(jobs)}")
    for i, j in enumerate(jobs[:7]):
        print(f"[LOG] {i+1} [{j['source']}] {j['company']} | {j['loc']} | {j['job_type_full']} | {j['title'][:40]}")
    return jobs

def is_posted(link):
    try:
        if not os.path.exists('posted.json'):
            return False
        with open('posted.json', 'r') as f:
            return link in json.load(f)
    except:
        return False

def save_link(link):
    try:
        d = []
        if os.path.exists('posted.json'):
            with open('posted.json', 'r') as f:
                d = json.load(f)
        d.append(link)
        with open('posted.json', 'w') as f:
            json.dump(d[-1000:], f)
    except:
        with open('posted.json', 'w') as f:
            json.dump([link], f)

def post_blogger_freshersvoice(job):
    try:
        uid = random.randint(10000, 99999)
        job['uid'] = str(uid)
        # Neat description - FreshersVoice style
        soup_desc = BeautifulSoup(job['desc'], 'html.parser').get_text()
        soup_desc = re.sub(r'\s+', ' ', soup_desc).strip()
        # Take only first 2 sentences for neat look
        sentences = soup_desc.split('. ')
        neat_desc = '. '.join(sentences[:3])[:700]
        now = datetime.now().strftime("%d %B %Y")
        html = f"""
<div style="font-family:Arial;line-height:1.9;max-width:820px;margin:auto;">
<p><b>HydHireHub</b> - {job['company']} {job['job_type_full']} 2026 for <b>{job['title']}</b> in {job['loc']}. {job['company']} hiring {job['job_type_short']} candidates from all over India - Hyd, Chennai, Bangalore, Pune, Vijayawada, Vizag.</p>
<table style="width:100%;border-collapse:collapse;margin:25px 0;border:1px solid #ddd;">
<tr><td style="padding:12px;background:#f1f5f9;font-weight:bold;width:32%;">Company Name</td><td style="padding:12px;"><b>{job['company']}</b></td></tr>
<tr><td style="padding:12px;background:#f1f5f9;font-weight:bold;">Job Type</td><td style="padding:12px;"><b>{job['job_type_full']}</b></td></tr>
<tr><td style="padding:12px;background:#f1f5f9;font-weight:bold;">Job Role</td><td style="padding:12px;"><b>{job['title']}</b></td></tr>
<tr><td style="padding:12px;background:#f1f5f9;font-weight:bold;">Location</td><td style="padding:12px;"><b>{job['loc']}</b></td></tr>
<tr><td style="padding:12px;background:#f1f5f9;font-weight:bold;">Qualification</td><td style="padding:12px;">{job['qual']}</td></tr>
<tr><td style="padding:12px;background:#f1f5f9;font-weight:bold;">Batch</td><td style="padding:12px;">{job['batch']}</td></tr>
<tr><td style="padding:12px;background:#f1f5f9;font-weight:bold;">Experience</td><td style="padding:12px;">{job['exp']}</td></tr>
</table>
<h3 style="color:#0f172a;border-left:4px solid #0d6efd;padding-left:12px;">Job Description - {job['company']} {job['loc']}</h3>
<p>{neat_desc}.</p>
<h3 style="color:#0f172a;border-left:4px solid #0d6efd;padding-left:12px;">Eligibility Criteria</h3>
<ul><li>Qualification: {job['qual']}</li><li>Batch: {job['batch']} - {job['batch']} Eligible</li><li>Location: {job['loc']} - Hyd, Chennai, Bangalore, Pune, Vijayawada, Vizag, Pan India</li><li>Experience: {job['exp']}</li></ul>
<h3 style="color:#0f172a;border-left:4px solid #0d6efd;padding-left:12px;">How to Apply</h3>
<ol><li>Click Apply Here button</li><li>Fill details on official page</li><li>Submit resume</li></ol>
<div style="text-align:center;margin:30px 0;"><a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:16px 50px;text-decoration:none;border-radius:8px;font-weight:bold;">🌐 Apply Here - HydHireHub</a></div>
<div style="background:#fef9c3;padding:14px;border-radius:8px;border-left:4px solid #eab308;"><b>Note:</b> No fee - {job['job_type_full']} - {job['loc']} - Only India - Direct company link.</div>
<p style="font-size:13px;color:#64748b;">Posted on {now} | HydHireHub | {job['job_type_full']} | {job['loc']} | Source: {job['source']}</p>
</div>
"""
        msg = MIMEText(html, "html")
        msg['Subject'] = f"HydHireHub | {job['company']} {job['job_type_full']} 2026 | {job['title']} | {job['loc']} | {uid}"
        msg['From'] = YOUR_GMAIL
        msg['To'] = BLOGGER_EMAIL
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(YOUR_GMAIL, APP_PASSWORD)
            s.send_message(msg)
        print(f"[LOG] BLOGGER SENT [{job['job_type_full']}] {job['company']} - {job['loc']}")
        return True
    except Exception as e:
        print(f"[LOG] BLOGGER FAIL {e}")
        return False

def get_blog_url(job):
    uid = job.get('uid', '')
    for _ in range(6):
        time.sleep(15)
        try:
            r = requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=10", timeout=15)
            soup = BeautifulSoup(r.text, 'xml')
            for item in soup.find_all('item'):
                if uid in item.title.text:
                    return item.find('link').text
        except:
            pass
    return BLOG_URL

def post_telegram(job, url):
    try:
        text = f"""🔥 {job['company']} {job['job_type_full']}

💼 {job['title']}
🏢 {job['company']}
📍 {job['loc']}
🎓 {job['qual']}

🌐 Apply:
{url}

https://t.me/HydHireHub
Only India - Hyd | Chennai | Bangalore | Pune | Vizag
"""
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHANNEL_ID, "text": text}, timeout=15)
    except:
        pass

try:
    print("[LOG] ===== HydHireHub Only India No Key Started =====")
    jobs = fetch_only_india_no_key()
    if not jobs:
        print("[LOG] No jobs")
        exit(0)
    for job in jobs:
        if is_posted(job['link']):
            continue
        if post_blogger_freshersvoice(job):
            url = get_blog_url(job)
            post_telegram(job, url)
            save_link(job['link'])
            break
    print("[LOG] ===== Finished =====")
    exit(0)
except Exception as e:
    print(f"[LOG] MAIN FAIL {e}")
    exit(0)
