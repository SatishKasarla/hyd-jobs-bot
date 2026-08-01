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
        return "Internship", "Internship"
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
    if "0-1" in text or "fresher" in text:
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
    if "mumbai" in full:
        return "Mumbai"
    if "vizag" in full or "visakhapatnam" in full:
        return "Vizag"
    if "vijayawada" in full:
        return "Vijayawada"
    if "delhi" in full or "noida" in full or "gurgaon" in full:
        return "Delhi NCR"
    if "work from home" in full or "wfh" in full or "remote" in full:
        return "Pan India (WFH)"
    return "Pan India"

def fetch_only_india_no_key():
    jobs = []
    print("[LOG] HydHireHub - ONLY INDIA - FINAL NO FAKE")
    blacklist = ["(m/f/d)", "(f/m/d)", "(m/w/d)", "(w/m/d)", "m/f/d", "m/w/d", "dach", "berlin", "munich", "germany", "deutschland", "für"]

    def is_allowed(title, desc, company):
        full = (title + " " + desc + " " + company).lower()
        for b in blacklist:
            if b in full:
                print(f"[LOG] BLOCKED FAKE/GERMAN: {title[:50]} -> {b}")
                return False
        if "westwing" in full:
            return False
        if "spacex" in full or "starlink" in full:
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
            if not is_allowed(title, desc, company):
                continue
            qual, batch, exp = parse_dynamic_full(desc, title)
            jt_full, jt_short, exp_text = detect_job_type(title, desc)
            loc = detect_location_simple(title, desc)
            jobs.append({"title": title[:90], "company": company or "Company", "link": link, "desc": desc, "qual": qual, "batch": batch, "exp": exp_text, "loc": loc, "job_type_full": jt_full, "job_type_short": jt_short, "source": "Jobicy"})
            c += 1
        print(f"[LOG] Jobicy India Geo Added: {c}")
        # Fallback if 0 - Fetch all remote and treat as Pan India
        if c == 0:
            print("[LOG] Jobicy India Geo 0 - Trying fallback all remote...")
            r2 = requests.get("https://jobicy.com/api/v2/remote-jobs?count=50", timeout=30).json()
            for j in r2.get('jobs', [])[:30]:
                title = j.get('jobTitle', '')
                desc = j.get('jobDescription', '')
                company = j.get('companyName', '')
                link = j.get('url', '')
                if not title or not link:
                    continue
                if not is_allowed(title, desc, company):
                    continue
                if "m/f/d" in title.lower() or "m/w/d" in title.lower():
                    continue
                qual, batch, exp = parse_dynamic_full(desc, title)
                jt_full, jt_short, exp_text = detect_job_type(title, desc)
                loc = detect_location_simple(title, desc)
                jobs.append({"title": title[:90], "company": company or "Company", "link": link, "desc": desc, "qual": qual, "batch": batch, "exp": exp_text, "loc": loc, "job_type_full": jt_full, "job_type_short": jt_short, "source": "Jobicy Fallback"})
                c += 1
                if c >= 10:
                    break
            print(f"[LOG] Jobicy Fallback Added: {c}")
        print(f"[LOG] Jobicy Total Added: {c}")
    except Exception as e:
        print(f"[LOG] Jobicy fail {e}")

    try:
        print("[LOG] Fetching Remotive India...")
        r = requests.get("https://remotive.com/api/remote-jobs?limit=50&search=india", timeout=30).json()
        c = 0
        for j in r.get('jobs', [])[:40]:
            title = j.get('title', '')
            desc = j.get('description', '')
            company = j.get('company_name', '')
            if not title:
                continue
            if not is_allowed(title, desc, company):
                continue
            qual, batch, exp = parse_dynamic_full(desc, title)
            jt_full, jt_short, exp_text = detect_job_type(title, desc)
            loc = detect_location_simple(title, desc)
            jobs.append({"title": title[:90], "company": company or "Company", "link": j.get('url', ''), "desc": desc, "qual": qual, "batch": batch, "exp": exp_text, "loc": loc, "job_type_full": jt_full, "job_type_short": jt_short, "source": "Remotive"})
            c += 1
            if c >= 10:
                break
        print(f"[LOG] Remotive Added: {c}")
    except Exception as e:
        print(f"[LOG] Remotive fail {e}")

    try:
        print("[LOG] Fetching ArbeitNow Remote...")
        r = requests.get("https://www.arbeitnow.com/api/job-board-api?search=india", timeout=25).json()
        c = 0
        for j in r.get('data', [])[:30]:
            title = j.get('title', '')
            desc = j.get('description', '')
            company = j.get('company_name', '')
            if not title:
                continue
            if not is_allowed(title, desc, company):
                continue
            qual, batch, exp = parse_dynamic_full(desc, title)
            jt_full, jt_short, exp_text = detect_job_type(title, desc)
            loc = detect_location_simple(title, desc)
            jobs.append({"title": title[:90], "company": company or "Company", "link": j.get('url', ''), "desc": desc, "qual": qual, "batch": batch, "exp": exp_text, "loc": loc, "job_type_full": jt_full, "job_type_short": jt_short, "source": "ArbeitNow"})
            c += 1
            if c >= 6:
                break
        print(f"[LOG] ArbeitNow Added: {c}")
    except Exception as e:
        print(f"[LOG] ArbeitNow fail {e}")

    random.shuffle(jobs)
    print(f"[LOG] FINAL READY: {len(jobs)} - No Fake Links")
    for i, j in enumerate(jobs[:5]):
        print(f"[LOG] {i+1} {j['company']} | {j['loc']} | {j['job_type_full']} | {j['title'][:40]}")
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
        soup_desc = BeautifulSoup(job['desc'], 'html.parser').get_text()
        soup_desc = re.sub(r'\s+', ' ', soup_desc).strip()
        sentences = soup_desc.split('. ')
        neat_desc = '. '.join(sentences[:3])[:750]
        now = datetime.now().strftime("%d %B %Y")
        html = f"""
<div style="font-family:Arial;line-height:1.9;max-width:800px;margin:auto;">
<h2 style="color:#0f172a;">{job['company']} {job['job_type_full']} 2026 | {job['title']}</h2>
<p><b>HydHireHub</b> - {job['company']} is conducting <b>{job['job_type_full']}</b> for <b>{job['title']}</b> in <b>{job['loc']}</b>. Eligible candidates can apply online.</p>
<table style="width:100%;border-collapse:collapse;margin:20px 0;border:1px solid #e2e8f0;font-size:15px;">
<tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:12px;background:#f8fafc;font-weight:bold;width:35%;border-right:1px solid #e2e8f0;">Company Name</td><td style="padding:12px;"><b>{job['company']}</b></td></tr>
<tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:12px;background:#f8fafc;font-weight:bold;border-right:1px solid #e2e8f0;">Job Role</td><td style="padding:12px;">{job['title']}</td></tr>
<tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:12px;background:#f8fafc;font-weight:bold;border-right:1px solid #e2e8f0;">Location</td><td style="padding:12px;"><b>{job['loc']}</b></td></tr>
<tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:12px;background:#f8fafc;font-weight:bold;border-right:1px solid #e2e8f0;">Qualification</td><td style="padding:12px;">{job['qual']}</td></tr>
<tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:12px;background:#f8fafc;font-weight:bold;border-right:1px solid #e2e8f0;">Batch</td><td style="padding:12px;">{job['batch']}</td></tr>
<tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:12px;background:#f8fafc;font-weight:bold;border-right:1px solid #e2e8f0;">Experience</td><td style="padding:12px;">{job['exp']}</td></tr>
<tr><td style="padding:12px;background:#f8fafc;font-weight:bold;border-right:1px solid #e2e8f0;">Job Type</td><td style="padding:12px;">{job['job_type_full']}</td></tr>
</table>
<h3 style="color:#1e293b;border-left:4px solid #0d6efd;padding-left:10px;">Job Description</h3>
<p>{neat_desc}.</p>
<h3 style="color:#1e293b;border-left:4px solid #0d6efd;padding-left:10px;">Eligibility Criteria</h3>
<ul style="line-height:1.9;"><li><b>Qualification:</b> {job['qual']}</li><li><b>Batch:</b> {job['batch']}</li><li><b>Location:</b> {job['loc']}</li><li><b>Experience:</b> {job['exp']}</li></ul>
<h3 style="color:#1e293b;border-left:4px solid #0d6efd;padding-left:10px;">How to Apply</h3>
<ol style="line-height:1.9;"><li>Click Apply Here</li><li>Go to official {job['company']} page</li><li>Fill form and submit</li></ol>
<div style="text-align:center;margin:30px 0;"><a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:14px 40px;text-decoration:none;border-radius:6px;font-weight:bold;display:inline-block;">Apply Now - {job['company']}</a></div>
<p style="background:#fff7ed;padding:12px;border-left:4px solid #f97316;font-size:14px;"><b>Note:</b> No fee - Only India jobs - Direct link - {job['loc']}.</p>
<p style="font-size:12px;color:#94a3b8;">Posted on {now} by HydHireHub | {job['loc']} Jobs | {job['job_type_full']}</p>
</div>
"""
        msg = MIMEText(html, "html")
        msg['Subject'] = f"{job['company']} {job['job_type_full']} 2026 | {job['title']} | {job['loc']} | {uid}"
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
        tag_loc = job['loc'].replace(' ', '').replace('(', '').replace(')', '').replace('/', '')
        text = f"""{job['company']} {job['job_type_full']} 2026 | {job['title']} | {job['loc']} | Apply Online

💼 Job Title: {job['title']}
🏢 Company: {job['company']}
📍 Location: {job['loc']}
🎓 Qualification: {job['qual']}
👨‍💻 Experience: {job['exp']}
🕒 Job Type: {job['job_type_full']}
💼 Batch: {job['batch']}

Apply now: {url}

{url}

#HydHireHub #FresherJobs #{tag_loc}Jobs #{job['job_type_full'].replace(' ', '').replace('-', '')}
"""
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHANNEL_ID, "text": text}, timeout=15)
        print(f"[LOG] TELEGRAM DONE - {job['loc']} - RealityDefine Style")
    except Exception as e:
        print(f"[LOG] Telegram fail {e}")

try:
    print("[LOG] ===== HydHireHub FINAL Started - No Fake Links =====")
    jobs = fetch_only_india_no_key()
    if not jobs:
        print("[LOG] No jobs today")
        exit(0)
    for job in jobs:
        if is_posted(job['link']):
            continue
        if post_blogger_freshersvoice(job):
            url = get_blog_url(job)
            post_telegram(job, url)
            save_link(job['link'])
            print(f"[LOG] SUCCESS - {job['company']} - {job['loc']}")
            break
    print("[LOG] ===== Finished OK - No (m/f/d) - No Fake =====")
    exit(0)
except Exception as e:
    print(f"[LOG] MAIN FAIL {e}")
    exit(0)
