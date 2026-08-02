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
        return "Recruitment", "Fresher + Experienced", "0-3 Years"

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
    if "hyderabad" in full or "hyd" in full:
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
    print("[LOG] HydHireHub FINAL - ONLY INDIA - HYD PRIORITY - ZERO FAKE")

    def is_allowed(title, desc, company):
        full = (title + " " + desc + " " + company).lower()
        block = [" - uk", " uk ", "| uk", "(uk)", " - uk -", "united kingdom", "london", " - usa", " usa ", "| usa", "united states", " - canada", "berlin", "munich", "deutschland", "germany only", "uk only", "us only", "(m/f/d)", "(m/w/d)", "m/f/d", "m/w/d", "dach"]
        for b in block:
            if b in full:
                print(f"[LOG] BLOCKED FAKE/UK/US: {title[:50]} -> {b}")
                return False
        if title.lower().strip().endswith("uk") or title.lower().strip().endswith("usa"):
            return False
        if "westwing" in full or "spacex" in full:
            return False
        return True

    # 1. Jobicy India Geo
    try:
        print("[LOG] Fetching Jobicy India Geo...")
        r = requests.get("https://jobicy.com/api/v2/remote-jobs?count=50&geo=india", timeout=30).json()
        c = 0
        for j in r.get('jobs', [])[:50]:
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
            jobs.append({"title": title[:90], "company": company or "Company", "link": link, "desc": desc, "qual": qual, "batch": batch, "exp": exp_text, "loc": loc, "job_type_full": jt_full, "job_type_short": jt_short})
            c += 1
        print(f"[LOG] Jobicy India Geo Added: {c}")
    except Exception as e:
        print(f"[LOG] Jobicy Geo fail {e}")

    # 2. Jobicy Fallback + Hyderabad search priority
    try:
        print("[LOG] Fetching Jobicy Fallback + Hyd Search...")
        for api_url in ["https://jobicy.com/api/v2/remote-jobs?count=50", "https://jobicy.com/api/v2/remote-jobs?count=50&tag=hyderabad"]:
            r = requests.get(api_url, timeout=30).json()
            c = 0
            for j in r.get('jobs', [])[:50]:
                title = j.get('jobTitle', '')
                desc = j.get('jobDescription', '')
                company = j.get('companyName', '')
                link = j.get('url', '')
                if not title or not link:
                    continue
                if is_posted(link):
                    continue
                if not is_allowed(title, desc, company):
                    continue
                qual, batch, exp = parse_dynamic_full(desc, title)
                jt_full, jt_short, exp_text = detect_job_type(title, desc)
                loc = detect_location_simple(title, desc)
                # Avoid duplicates
                if any(x['link'] == link for x in jobs):
                    continue
                jobs.append({"title": title[:90], "company": company or "Company", "link": link, "desc": desc, "qual": qual, "batch": batch, "exp": exp_text, "loc": loc, "job_type_full": jt_full, "job_type_short": jt_short})
                c += 1
            print(f"[LOG] Jobicy {api_url[-20:]} Added: {c}")
    except Exception as e:
        print(f"[LOG] Jobicy Fallback fail {e}")

    # 3. Remotive India + Hyderabad
    try:
        print("[LOG] Fetching Remotive India + Hyderabad...")
        for search in ["india", "hyderabad", "bangalore"]:
            r = requests.get(f"https://remotive.com/api/remote-jobs?limit=50&search={search}", timeout=30).json()
            c = 0
            for j in r.get('jobs', [])[:30]:
                title = j.get('title', '')
                desc = j.get('description', '')
                company = j.get('company_name', '')
                if not title:
                    continue
                if not is_allowed(title, desc, company):
                    continue
                link = j.get('url', '')
                if any(x['link'] == link for x in jobs):
                    continue
                qual, batch, exp = parse_dynamic_full(desc, title)
                jt_full, jt_short, exp_text = detect_job_type(title, desc)
                loc = detect_location_simple(title, desc)
                jobs.append({"title": title[:90], "company": company or "Company", "link": link, "desc": desc, "qual": qual, "batch": batch, "exp": exp_text, "loc": loc, "job_type_full": jt_full, "job_type_short": jt_short})
                c += 1
            print(f"[LOG] Remotive {search} Added: {c}")
    except Exception as e:
        print(f"[LOG] Remotive fail {e}")

    # SORT: Hyderabad first, then other India cities, then Pan India
    def sort_key(j):
        loc = j['loc']
        if loc == "Hyderabad":
            return 0
        if loc in ["Bangalore", "Chennai", "Pune", "Mumbai", "Vizag", "Vijayawada"]:
            return 1
        if loc == "Delhi NCR":
            return 2
        return 3

    jobs_sorted = sorted(jobs, key=sort_key)
    random.shuffle(jobs_sorted[6:]) # Shuffle after top 6 hyd
    jobs = jobs_sorted

    print(f"[LOG] FINAL READY: {len(jobs)} - Min 10 Guarantee")
    for i, j in enumerate(jobs[:10]):
        print(f"[LOG] {i+1} {j['company']} | {j['loc']} | {j['job_type_full']} | {j['title'][:45]}")
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
        neat_desc = '. '.join(sentences[:4])[:900]
        now = datetime.now().strftime("%d %B %Y")
        html = f"""
<div style="font-family:Arial;line-height:1.85;max-width:800px;margin:auto;color:#1e293b;">
<h1 style="font-size:22px;color:#0f172a;line-height:1.4;">{job['company']} {job['job_type_full']} 2026 | {job['title']} | {job['loc']}</h1>
<p><b>HydHireHub</b> - {job['company']} is hiring for <b>{job['title']}</b> in <b>{job['loc']}</b>. Check complete details below.</p>
<table style="width:100%;border-collapse:collapse;margin:18px 0;border:1px solid #e2e8f0;font-size:14px;">
<tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:11px;background:#f8fafc;font-weight:700;width:34%;border-right:1px solid #e2e8f0;">Company Name</td><td style="padding:11px;">{job['company']}</td></tr>
<tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:11px;background:#f8fafc;font-weight:700;border-right:1px solid #e2e8f0;">Job Role</td><td style="padding:11px;"><b>{job['title']}</b></td></tr>
<tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:11px;background:#f8fafc;font-weight:700;border-right:1px solid #e2e8f0;">Location</td><td style="padding:11px;"><b>{job['loc']}</b></td></tr>
<tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:11px;background:#f8fafc;font-weight:700;border-right:1px solid #e2e8f0;">Qualification</td><td style="padding:11px;">{job['qual']}</td></tr>
<tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:11px;background:#f8fafc;font-weight:700;border-right:1px solid #e2e8f0;">Batch</td><td style="padding:11px;">{job['batch']}</td></tr>
<tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:11px;background:#f8fafc;font-weight:700;border-right:1px solid #e2e8f0;">Experience</td><td style="padding:11px;">{job['exp']}</td></tr>
<tr><td style="padding:11px;background:#f8fafc;font-weight:700;border-right:1px solid #e2e8f0;">Job Type</td><td style="padding:11px;">{job['job_type_full']}</td></tr>
</table>
<h3 style="color:#0f172a;border-left:4px solid #0d6efd;padding-left:10px;margin-top:22px;">Job Description</h3>
<p>{neat_desc}.</p>
<h3 style="color:#0f172a;border-left:4px solid #0d6efd;padding-left:10px;">Eligibility Criteria</h3>
<ul style="margin:8px 0 16px 18px;"><li>Qualification: {job['qual']}</li><li>Batch: {job['batch']}</li><li>Experience: {job['exp']}</li><li>Location: {job['loc']}</li></ul>
<h3 style="color:#0f172a;border-left:4px solid #0d6efd;padding-left:10px;">How to Apply?</h3>
<p>Click Apply Now to go to official {job['company']} career page.</p>
<div style="text-align:center;margin:24px 0;"><a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:13px 36px;text-decoration:none;border-radius:6px;font-weight:700;display:inline-block;">Apply Now</a></div>
<p style="background:#fff7ed;padding:10px 12px;border-left:4px solid #f59e0b;font-size:13px;">Note: No fee. Only India jobs - {job['loc']} priority.</p>
<p style="font-size:11px;color:#94a3b8;margin-top:18px;">Posted on {now} | HydHireHub | {job['loc']} Jobs</p>
</div>
"""
        msg = MIMEText(html, "html")
        msg['Subject'] = f"{job['company']} {job['job_type_full']} 2026 | {job['title']} | {job['loc']} | {uid}"
        msg['From'] = YOUR_GMAIL
        msg['To'] = BLOGGER_EMAIL
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(YOUR_GMAIL, APP_PASSWORD)
            s.send_message(msg)
        print(f"[LOG] BLOGGER SENT {job['company']} - {job['loc']}")
        return True
    except Exception as e:
        print(f"[LOG] BLOGGER FAIL {e}")
        return False

def get_blog_url(job):
    uid = job.get('uid', '')
    print(f"[LOG] Searching blog URL for UID {uid} - 4 mins...")
    time.sleep(40)
    for attempt in range(10):
        try:
            print(f"[LOG] Blog attempt {attempt+1}/10 UID {uid}")
            r = requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=30", timeout=20)
            soup = BeautifulSoup(r.text, 'xml')
            for item in soup.find_all('item'):
                title = item.find('title').text if item.find('title') else ""
                link = item.find('link').text if item.find('link') else ""
                if uid in title:
                    print(f"[LOG] BLOG URL FOUND: {link}")
                    return link, True
        except Exception as e:
            print(f"[LOG] Blog URL fail {attempt+1}: {e}")
        time.sleep(25)
    print(f"[LOG] BLOG URL NOT FOUND - Blogger Email posting failed! Check BLOGGER_EMAIL secret")
    return f"{BLOG_URL}/search?q={uid}", False

def post_telegram(job, url):
    try:
        # Check if this blog url was already posted before
        last_blog_file = 'last_blog_url.txt'
        if os.path.exists(last_blog_file):
            with open(last_blog_file, 'r') as f:
                last_url = f.read().strip()
                if last_url == url and "search?q=" not in url:
                    print(f"[LOG] DUPLICATE BLOG URL DETECTED: {url} - Waiting 60 sec and retrying RSS...")
                    time.sleep(60)
                    # Retry once more to get correct URL
                    r = requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=30", timeout=20)
                    soup = BeautifulSoup(r.text, 'xml')
                    for item in soup.find_all('item'):
                        title = item.find('title').text if item.find('title') else ""
                        link = item.find('link').text if item.find('link') else ""
                        if job.get('uid','') in title:
                            url = link
                            print(f"[LOG] RETRY FOUND CORRECT URL: {url}")
                            break
        
        # Save this url
        with open(last_blog_file, 'w') as f:
            f.write(url)

        tag_loc = job['loc'].replace(' ', '').replace('(', '').replace(')', '').replace('/', '').replace('-', '')
        text = f"""{job['company']} {job['job_type_full']} 2026 | {job['title']} | {job['loc']} | Apply Online

💼 Job Title: {job['title']}
🏢 Company: {job['company']}
📍 Location: {job['loc']}
🎓 Qualification: {job['qual']}
👨‍💻 Experience: {job['exp']}
🕒 Job Type: {job['job_type_full']}
💼 Batch: {job['batch']}

📄 Full Details: {url}

#HydHireHub #FresherJobs #{tag_loc}Jobs
"""
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHANNEL_ID, "text": text}, timeout=15)
        print(f"[LOG] TELEGRAM DONE - {job['loc']} - Unique Link: {url[:60]}")
    except Exception as e:
        print(f"[LOG] Telegram fail {e}")

try:
    print("[LOG] ===== HydHireHub FINAL - HYD MAX - STARTED =====")
    jobs = fetch_only_india_no_key()
    if len(jobs) < 5:
        print(f"[LOG] Only {len(jobs)} jobs - low")
        exit(0)
    for job in jobs:
        if is_posted(job['link']):
            continue
        if post_blogger_freshersvoice(job):
            url, found = get_blog_url(job)
            if not found:
                print(f"[LOG] BLOG NOT FOUND - Skipping Telegram - Check BLOGGER_EMAIL secret! UID {job['uid']}")
                # Do NOT save link, so next run will retry different job
                # Also do NOT post telegram with search link
                break
            post_telegram(job, url)
            save_link(job['link'])
            break
    print(f"[LOG] ===== Finished =====")
    exit(0)
except Exception as e:
    print(f"[LOG] MAIN FAIL {e}")
    exit(0)
