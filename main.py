import requests, json, os, smtplib, re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# --- SECRETS FROM GITHUB ---
ADZUNA_ID = os.environ['ADZUNA_APP_ID']
ADZUNA_KEY = os.environ['ADZUNA_APP_KEY']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
GMAIL_USER = os.environ['GMAIL_USER']
GMAIL_PASS = os.environ['GMAIL_PASS'] # 16 digit App Password
BLOGGER_EMAIL = os.environ['BLOGGER_EMAIL']

# --- FILTERS ---
BLACKLIST = ["data entry", "work from home earn", "packing", "without investment", "call boy", "part time earn", "earn money", "captcha", "typing work", "investment"]
GOOD_KEYWORDS = ["developer", "engineer", "support", "analyst", "executive", "associate", "designer", "tester", "manager", "fresher", "trainee", "intern"]

def is_good_job(job):
    title = job['title'].lower()
    desc = job.get('description', '').lower()
    company = job['company']['display_name'].lower()
    
    # 1. Blacklist check - Fake jobs cut
    if any(b in title or b in desc for b in BLACKLIST):
        print(f"SKIPPED Blacklist: {title}")
        return False
    # 2. Location check - Only Hyderabad, India
    loc = job['location']['display_name'].lower()
    if "hyderabad" not in loc:
        return False
    if "pakistan" in loc or "sindh" in loc:
        return False
    # 3. Company name undali
    if len(company) < 2 or company == "confidential":
        return False
    # 4. Description chala chinna ga unte fake
    if len(desc) < 200:
        return False
    return True

def get_new_jobs():
    url = f"https://api.adzuna.com/v1/api/jobs/in/search/1?app_id={ADZUNA_ID}&app_key={ADZUNA_KEY}&results_per_page=30&where=Hyderabad&sort_by=date&max_days_old=1"
    res = requests.get(url).json()
    
    try:
        with open('posted.json') as f:
            posted = json.load(f)
    except:
        posted = []
    
    new_jobs = []
    for job in res.get('results', []):
        job_id = str(job['id'])
        if job_id in posted:
            continue
        if not is_good_job(job):
            continue
        new_jobs.append(job)
        posted.append(job_id)
    
    # Duplicate save chey
    with open('posted.json', 'w') as f:
        json.dump(posted, f)
    return new_jobs[:5] # Roju max 5 jobs matrame - Spam avvakunda

def post_to_blogger(job):
    title = f"{job['title']} - {job['company']['display_name']} | Hyderabad Jobs 2026"
    salary = f"{job.get('salary_min', 'Not Disclosed')} - {job.get('salary_max', '')}" if job.get('salary_min') else "Not Disclosed"
    
    # Blogger ki manchi ga kanipinchadaniki HTML
    html = f"""
    <h2>{job['title']}</h2>
    <p><b>Company:</b> {job['company']['display_name']}</p>
    <p><b>Location:</b> {job['location']['display_name']}</p>
    <p><b>Salary:</b> {salary}</p>
    <p><b>Posted On:</b> {datetime.now().strftime('%d %B %Y')}</p>
    <h3>Job Description</h3>
    <p>{job['description'][:1500]}</p>
    <h3>How to Apply</h3>
    <p>Kindly click on the below Apply Now button to apply on official website.</p>
    <p><a href="{job['redirect_url']}" target="_blank"><b>👉 CLICK HERE TO APPLY NOW</b></a></p>
    <p><i>Note: Please verify all details on official website before applying.</i></p>
    """
    
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = BLOGGER_EMAIL
    msg['Subject'] = title
    msg.attach(MIMEText(html, 'html'))
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(GMAIL_USER, GMAIL_PASS)
    server.send_message(msg)
    server.quit()
    print(f"BLOGGER POSTED: {title}")
    # Blog link manam exact ga teliyadu kabatti, homepage link istham
    return "https://hydhirehub.blogspot.com/"

def send_to_telegram(job, blog_link):
    salary = f"{job.get('salary_min', 'Not Disclosed')}" if job.get('salary_min') else "Not Disclosed"
    message = f"""
🔥 *{job['title']}*

🏢 Company: {job['company']['display_name']}
📍 Location: {job['location']['display_name']}
💰 Salary: {salary}

📝 Full Details:
👉 {blog_link}

🔗 Direct Apply:
👉 {job['redirect_url']}

#HyderabadJobs #HydHireHub #JobsInHyderabad
"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)
    print(f"TELEGRAM POSTED: {job['title']}")

if __name__ == "__main__":
    jobs = get_new_jobs()
    print(f"Found {len(jobs)} good jobs")
    for job in jobs:
        try:
            blog_link = post_to_blogger(job)
            send_to_telegram(job, blog_link)
        except Exception as e:
            print(f"Error: {e}")
