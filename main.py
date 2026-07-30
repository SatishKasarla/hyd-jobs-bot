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
    try:
        text = (title + " " + desc).lower()
        if "mba" in text:
            qual = "B.E/B.Tech/MBA/MCA/Any Graduate"
        elif "bca" in text or "bsc" in text:
            qual = "B.E/B.Tech/B.Sc/BCA/MCA"
        else:
            qual = "B.E/B.Tech/M.Tech/MCA/Any Degree"
        years = re.findall(r'202[0-3]|202[4-6]', text)
        if years:
            batch = "/".join(sorted(list(set(years)))[:5])
        else:
            batch = "2023/2024/2025/2026"
        if "2+ years" in text or "3+ years" in text:
            exp = "Experienced (2+ Years)"
        elif "0-1" in text or "fresher" in text.lower():
            exp = "Freshers (0-1 Year)"
        else:
            exp = "0-3 Years (Freshers + Experienced)"
        return qual, batch, exp
    except Exception as e:
        print(f"Parse fail {e}")
        return "B.E/B.Tech/MCA", "2024/2025/2026", "0-3 Years"

def fetch_hyd_only():
    jobs = []
    print("[LOG] Fetching ONLY Hyderabad + India Eligible - UK/DE/US BLOCKED")

    blacklist = ["uk only", "germany only", "europe only", "eu only", "us only", "usa only", "united kingdom", "deutschland", "berlin", "london", "dach", "european", "us citizen", "uk citizen", "german language"]

    def is_valid_job(title, desc):
        try:
            full = (title + " " + desc).lower()
            for bad in blacklist:
                if bad in full and "india" not in full and "hyderabad" not in full:
                    return False, "blocked"
            if "hyderabad" in full:
                return True, "Hyderabad"
            if "india" in full:
                return True, "Remote - Hyderabad Eligible"
            return False, "no"
        except:
            return False, "no"

    # 1. Jobicy - India geo - main source
    try:
        print("[LOG] Trying Jobicy...")
        r = requests.get("https://jobicy.com/api/v2/remote-jobs?count=50&geo=india", timeout=25)
        data = r.json()
        all_jobs = data.get('jobs', [])
        print(f"[LOG] Jobicy total India jobs: {len(all_jobs)}")
        for j in all_jobs:
            try:
                title = j.get('jobTitle', '')
                desc = j.get('jobDescription', '')
                company = j.get('companyName', 'Company')
                link = j.get('url', '')
                if not title or not link:
                    continue
                if any(x in title.lower() for x in ["für", "ä", "ö", "ß", "dach"]):
                    continue
                valid, loc = is_valid_job(title, desc)
                if not valid:
                    continue
                qual, batch, exp = parse_dynamic(desc, title)
                jobs.append({
                    "title": title[:80],
                    "company": company,
                    "link": link,
                    "desc": desc,
                    "qual": qual,
                    "batch": batch,
                    "exp": exp,
                    "loc": loc,
                    "source": "Jobicy"
                })
            except Exception as e:
                continue
        print(f"[LOG] Jobicy after filter Hyd: {len(jobs)}")
    except Exception as e:
        print(f"[LOG] Jobicy main fail {e}")

    # 2. Remotive - India + Hyd only - UK DE block
    try:
        print("[LOG] Trying Remotive...")
        r = requests.get("https://remotive.com/api/remote-jobs?limit=80", timeout=25)
        data = r.json()
        rem_jobs = data.get('jobs', [])
        print(f"[LOG] Remotive total: {len(rem_jobs)}")
        c = 0
        for j in rem_jobs:
            try:
                title = j.get('title', '')
                desc = j.get('description', '')
                if not title:
                    continue
                if "senior sales manager dach" in title.lower():
                    continue
                if any(x in title.lower() for x in ["für", "ä", "ö", "ß", "german"]):
                    continue
                valid, loc = is_valid_job(title, desc)
                if not valid:
                    continue
                qual, batch, exp = parse_dynamic(desc, title)
                jobs.append({
                    "title": title[:80],
                    "company": j.get('company_name', 'Company'),
                    "link": j.get('url', ''),
                    "desc": desc,
                    "qual": qual,
                    "batch": batch,
                    "exp": exp,
                    "loc": loc,
                    "source": "Remotive"
                })
                c += 1
                if c >= 5:
                    break
            except:
                continue
        print(f"[LOG] Remotive Hyd filtered: {c} | Total now: {len(jobs)}")
    except Exception as e:
        print(f"[LOG] Remotive fail {e}")

    # 3. ArbeitNow - Extra
    try:
        print("[LOG] Trying ArbeitNow...")
        r = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=25)
        data = r.json()
        arb_jobs = data.get('data', [])
        c = 0
        for j in arb_jobs[:40]:
            try:
                title = j.get('title', '')
                desc = j.get('description', '')
                full = (title + desc).lower()
                if "hyderabad" not in full and "india" not in full:
                    continue
                if any(x in full for x in ["uk only", "germany", "berlin", "london"]):
                    continue
                valid, loc = is_valid_job(title, desc)
                if not valid:
                    continue
                qual, batch, exp = parse_dynamic(desc, title)
                jobs.append({
                    "title": title[:80],
                    "company": j.get('company_name', 'Company'),
                    "link": j.get('url', ''),
                    "desc": desc,
                    "qual": qual,
                    "batch": batch,
                    "exp": exp,
                    "loc": loc,
                    "source": "ArbeitNow"
                })
                c += 1
                if c >= 3:
                    break
            except:
                continue
        print(f"[LOG] ArbeitNow added: {c} | Total: {len(jobs)}")
    except Exception as e:
        print(f"[LOG] ArbeitNow fail {e}")

    random.shuffle(jobs)
    print(f"[LOG] TOTAL FINAL HYD ONLY READY (UK/DE/US BLOCKED): {len(jobs)}")
    for idx, j in enumerate(jobs[:5]):
        print(f"[LOG] {idx+1} -> {j['source']} | {j['company']} | {j['loc']} | {j['title'][:50]}")
    return jobs

def is_already_in_blog(company, title):
    try:
        r = requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=30", timeout=15)
        soup = BeautifulSoup(r.text, 'xml')
        for item in soup.find_all('item'):
            t = item.title.text.lower()
            if company.split()[0].lower() in t and title.split()[0].lower() in t:
                return True
    except Exception as e:
        print(f"Blog check fail {e}")
    return False

def is_posted(link):
    try:
        if not os.path.exists('posted.json'):
            return False
        with open('posted.json', 'r') as f:
            data = json.load(f)
            return link in data
    except:
        return False

def save_link(link):
    try:
        d = []
        if os.path.exists('posted.json'):
            try:
                with open('posted.json', 'r') as f:
                    d = json.load(f)
            except:
                d = []
        d.append(link)
        with open('posted.json', 'w') as f:
            json.dump(d[-1000:], f)
        print(f"[LOG] Saved to posted.json: {link[:50]}")
    except Exception as e:
        print(f"Save fail {e}")
        try:
            with open('posted.json', 'w') as f:
                json.dump([link], f)
        except:
            pass

def post_blogger(job):
    try:
        uid = random.randint(10000, 99999)
        job['uid'] = str(uid)
        now = datetime.now().strftime("%d %B %Y")

        clean_desc = BeautifulSoup(job['desc'], 'html.parser').get_text()
        clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
        clean_desc = clean_desc[:700]

        if "Fresher" in job['exp']:
            drive_type = "Off Campus Drive"
        else:
            drive_type = "Hiring / Recruitment"

        html = f"""
<div style="font-family:Arial,sans-serif;line-height:1.9;max-width:800px;margin:auto;color:#222;">
<p>{job['company']} {drive_type} for {job['title']} in Hyderabad. {job['company']} is hiring for the position of {job['title']} Profile. Complete information mentioned below:</p>

<table style="width:100%;border-collapse:collapse;margin:25px 0;border:1px solid #ddd;font-size:15px;">
<tr style="border-bottom:1px solid #ddd;"><td style="padding:14px 16px;background:#f8f9fa;font-weight:bold;width:35%;border-right:1px solid #ddd;">Company Name</td><td style="padding:14px 16px;"><b>{job['company']}</b></td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:14px 16px;background:#f8f9fa;font-weight:bold;border-right:1px solid #ddd;">Profile Hiring for</td><td style="padding:14px 16px;"><b>{job['title']}</b></td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:14px 16px;background:#f8f9fa;font-weight:bold;border-right:1px solid #ddd;">Salary</td><td style="padding:14px 16px;">As Per Market Standards</td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:14px 16px;background:#f8f9fa;font-weight:bold;border-right:1px solid #ddd;">Work Profile</td><td style="padding:14px 16px;">Work from Office - Hyderabad</td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:14px 16px;background:#f8f9fa;font-weight:bold;border-right:1px solid #ddd;">Eligibility</td><td style="padding:14px 16px;">{job['exp']}</td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:14px 16px;background:#f8f9fa;font-weight:bold;border-right:1px solid #ddd;">Location</td><td style="padding:14px 16px;"><b>{job['loc']}</b></td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:14px 16px;background:#f8f9fa;font-weight:bold;border-right:1px solid #ddd;">Qualification</td><td style="padding:14px 16px;">{job['qual']}</td></tr>
<tr style="border-bottom:1px solid #ddd;"><td style="padding:14px 16px;background:#f8f9fa;font-weight:bold;border-right:1px solid #ddd;">Batch</td><td style="padding:14px 16px;">{job['batch']}</td></tr>
<tr><td style="padding:14px 16px;background:#f8f9fa;font-weight:bold;border-right:1px solid #ddd;">Job ID</td><td style="padding:14px 16px;">HH{uid}</td></tr>
</table>

<h3 style="margin-top:35px;color:#0d2a54;">Eligibility Criteria for {job['company']} {drive_type}</h3>
<p>{job['company']} is a leading organization delivering innovative solutions. Your work will directly impact growth. Join us to start <b>Caring. Connecting. Growing together.</b></p>

<p><b>Primary Responsibilities:</b></p>
<ul style="padding-left:22px;">
<li>Work on {job['title']} role for Hyderabad location</li>
<li>{clean_desc}</li>
<li>Collaborate with cross-functional teams to deliver quality results</li>
<li>Increase efficiency and effectiveness of overall operations</li>
<li>Open to work in Hyderabad / Hybrid environment as per guidelines</li>
</ul>

<p><b>Required Qualifications:</b></p>
<ul style="padding-left:22px;">
<li>{job['qual']} from recognized university</li>
<li>Eligibility: {job['exp']} - Relevant experience is added advantage</li>
<li>Good communication and analytical skills</li>
<li>Ability to work independently and share status updates</li>
<li>Batch Eligible: {job['batch']}</li>
</ul>

<h3 style="margin-top:35px;color:#0d2a54;">How to Apply for {job['company']} Recruitment</h3>
<ol style="padding-left:22px;">
<li>Click on the "<b>Apply here</b>" button below. You will be redirected to application page.</li>
<li>Fill in the application form with all necessary details.</li>
<li>Submit all relevant documents, if required.</li>
<li>Make sure that all details entered are correct.</li>
<li>Submit the application form & wait for company's revert.</li>
</ol>

<div style="text-align:center;margin:40px 0;">
<a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:16px 45px;text-decoration:none;border-radius:8px;font-weight:bold;font-size:18px;display:inline-block;">🌐 Apply Here - {job['company']}</a>
</div>

<p style="background:#fff3cd;padding:14px;border-radius:8px;"><b>IMPORTANT INFORMATION:</b><br>No fee Charged from candidates / Never pay any amount for getting a job.<br><br><b>Many employers prefer Applications on First come First Serve Basis. Apply immediately once the job is posted.</b></p>
<p style="font-size:13px;color:#666;"><i>Posted on {now} | Source: {job['source']} | {drive_type} | Location: Hyderabad Only</i></p>
</div>
"""
        msg = MIMEText(html, "html")
        msg['Subject'] = f"{job['company']} {drive_type} {job['title']} - Hyderabad Jobs {uid}"
        msg['From'] = YOUR_GMAIL
        msg['To'] = BLOGGER_EMAIL
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(YOUR_GMAIL, APP_PASSWORD)
            s.send_message(msg)
        print(f"[LOG] BLOGGER SENT UID:{uid} - {job['company']} - {drive_type} - Clean")
        return True
    except Exception as e:
        print(f"[LOG] BLOGGER FAIL {e}")
        return False

def get_blog_url(job):
    uid = job.get('uid', '')
    print(f"[LOG] Searching UID {uid} - wait 10 mins for blog")
    for attempt in range(12):
        time.sleep(25)
        try:
            r = requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=15", timeout=20)
            soup = BeautifulSoup(r.text, 'xml')
            for item in soup.find_all('item'):
                if uid in item.title.text:
                    link = item.find('link').text
                    print(f"[LOG] CORRECT URL FOUND AFTER {attempt+1} TRIES: {link}")
                    return link
        except Exception as e:
            print(f"RSS fail {e}")
        print(f"[LOG] Try {attempt+1}/12 - not found yet, waiting...")
    print("[LOG] UID not found after 10 mins - using blog homepage")
    return BLOG_URL

def post_telegram(job, url):
    try:
        drive = "Off Campus Drive" if "Fresher" in job['exp'] else "Hiring"
        text = f"""🔥 {job['company']} {drive} 2026

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
        r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHANNEL_ID, "text": text}, timeout=15)
        print(f"[LOG] TELEGRAM POSTED: {url} | Status: {r.status_code}")
    except Exception as e:
        print(f"[LOG] Telegram fail {e}")

# MAIN EXECUTION
try:
    print("[LOG] ===== BOT STARTED =====")
    jobs = fetch_hyd_only()
    print(f"[LOG] Jobs fetched: {len(jobs)}")
    if not jobs:
        print("[LOG] No Hyderabad jobs today - will retry after 6 hours")
        exit(0)
    posted = 0
    for job in jobs:
        try:
            if is_posted(job['link']):
                print(f"[LOG] Already posted: {job['company']}")
                continue
            if is_already_in_blog(job['company'], job['title']):
                print(f"[LOG] Already in blog: {job['company']}")
                save_link(job['link'])
                continue
            if post_blogger(job):
                url = get_blog_url(job)
                post_telegram(job, url)
                save_link(job['link'])
                print(f"[LOG] SUCCESS - {job['company']} - HYD ONLY - VINKJOBS STYLE")
                posted += 1
                break
        except Exception as e:
            print(f"[LOG] Job loop fail {e}")
            continue
    if posted == 0:
        print("[LOG] No new job posted - all already posted")
    print("[LOG] ===== BOT FINISHED OK =====")
    exit(0)
except Exception as e:
    print(f"[LOG] MAIN CRITICAL FAIL {e}")
    exit(0)
