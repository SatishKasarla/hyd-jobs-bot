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

    # Qualification dynamic
    if "mba" in text: qual = "B.E/B.Tech/MBA/MCA"
    elif "bca" in text: qual = "B.E/B.Tech/B.Sc/BCA/MCA"
    else: qual = "B.E/B.Tech/M.Tech/MCA"

    # Batch 2020-2026 dynamic - job lo 2020 unte 2020 ye vasthadi
    years = re.findall(r'202[0-6]', text) # 2020,2021,2022,2023,2024,2025,2026
    if years:
        uniq = sorted(list(set(years)))
        batch = "/".join(uniq[:4]) # Max 4 years
    else:
        batch = "2024/2025/2026" # Default if no year in description

    # Experience dynamic
    if "0-1" in text or "fresher" in text or "0 year" in text: exp = "Freshers (0-1 Year)"
    elif "1-2 year" in text or "2 year" in text: exp = "0-2 Years"
    elif "3-5" in text: exp = "2-5 Years"
    else: exp = "Freshers"

    # Location dynamic - Hyd vs Remote
    if "hyderabad" in text and "remote" in text:
        loc = "Remote / Hyderabad"
    elif "hyderabad" in text:
        loc = "Hyderabad"
    elif "remote" in text:
        loc = "Remote"
    elif "bangalore" in text:
        loc = "Bangalore" # Skip ayyela chestham kindha
    else:
        loc = "Hyderabad" # Default
    return qual, batch, exp, loc

def fetch_only_hyd():
    jobs=[]
    # 1. Jobicy - Filter Hyd only
    try:
        r=requests.get("https://jobicy.com/api/v2/remote-jobs?count=50&geo=india", timeout=20).json()
        for j in r.get('jobs',[]):
            title=j.get('jobTitle',''); desc=j.get('jobDescription',''); company=j.get('companyName','')
            full_text = (title+" "+desc).lower()
            # ONLY HYD FILTER
            if "hyderabad" not in full_text and "remote" not in full_text:
                continue # Hyd ledu Remote ledu - skip
            if "bangalore" in full_text and "hyderabad" not in full_text:
                continue # Only Bangalore - skip
            if any(x in title.lower() for x in ["für","ä","ö","ß"]): continue

            qual,batch,exp,loc = parse_dynamic(desc, title)
            # Only allow Hyd or Remote
            if loc not in ["Hyderabad","Remote","Remote / Hyderabad"]:
                continue

            jobs.append({"title":title[:70],"company":company,"link":j['url'],"desc":desc[:800],"qual":qual,"batch":batch,"exp":exp,"loc":loc,"source":"Jobicy"})
        print(f"[LOG] Jobicy Hyd/Remote: {len(jobs)}")
    except Exception as e: print(f"Jobicy fail {e}")

    # 2. Remotive - Hyd/Remote only
    try:
        r=requests.get("https://remotive.com/api/remote-jobs?limit=50", timeout=20).json()
        c=0
        for j in r['jobs']:
            full = (j.get('title','')+j.get('description','')+j.get('candidate_required_location','')).lower()
            if "hyderabad" not in full and "india" not in full: continue
            if "bangalore" in full and "hyderabad" not in full: continue
            qual,batch,exp,loc = parse_dynamic(j['description'], j['title'])
            if loc not in ["Hyderabad","Remote","Remote / Hyderabad"]: loc="Remote"
            jobs.append({"title":j['title'][:70],"company":j['company_name'],"link":j['url'],"desc":j['description'][:800],"qual":qual,"batch":batch,"exp":exp,"loc":loc,"source":"Remotive"})
            c+=1
        print(f"[LOG] Remotive Hyd: {c}")
    except Exception as e: print(f"Remotive fail {e}")

    # 3. ArbeitNow - Hyd only filtered
    try:
        r=requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=20).json()
        c=0
        for j in r['data']:
            full=(j.get('title','')+j.get('description','')+j.get('location','')).lower()
            if "hyderabad" not in full and "india" not in full: continue
            if "bangalore" in full and "hyderabad" not in full: continue
            if any(x in full for x in ["für","ä","ö","ü","unser"]): continue
            qual,batch,exp,loc = parse_dynamic(j.get('description',''), j.get('title',''))
            jobs.append({"title":j.get('title','')[:70],"company":j.get('company_name','Company'),"link":j.get('url',''),"desc":j.get('description','')[:800],"qual":qual,"batch":batch,"exp":exp,"loc":loc,"source":"ArbeitNow"})
            c+=1
            if c>=5: break
        print(f"[LOG] ArbeitNow Hyd: {c}")
    except Exception as e: print(f"ArbeitNow fail {e}")

    random.shuffle(jobs)
    print(f"[LOG] TOTAL HYD JOBS: {len(jobs)}")
    for j in jobs[:5]: print(f"[LOG] -> {j['company']} | {j['loc']} | Batch:{j['batch']} | {j['title']}")
    return jobs

def is_already_in_blog(company, title):
    try:
        r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=30", timeout=15)
        soup=BeautifulSoup(r.text,'xml')
        for item in soup.find_all('item'):
            t=item.title.text.lower()
            if company.split()[0].lower() in t and title.split()[0].lower() in t: return True
    except: pass
    return False

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
    uid=random.randint(1000,9999)
    html=f"""<div style="font-family:Arial;line-height:1.8;"><h1>{job['company']} Hiring {job['title']} - {job['loc']} 2026</h1><p><b>Hyd Jobs Real:</b> {job['company']} hiring {job['title']} in {job['loc']}.</p><div style="background:#eef2ff;padding:15px;border-radius:8px;"><p>💼 Job Role: {job['title']}<br>🏢 Company: {job['company']}<br>🎓 Qualification: {job['qual']}<br>🔹 Batch: {job['batch']}<br>🆕 Experience: {job['exp']}<br>📍 Location: {job['loc']}</p></div><p>{job['desc'][:800]}</p><div style="text-align:center;margin:25px;"><a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:16px 45px;text-decoration:none;border-radius:8px;font-weight:bold;">🌐 Apply Here</a></div></div>"""
    msg=MIMEText(html,"html")
    msg['Subject']=f"{job['company']} {job['title']} {job['loc']} {uid}"
    msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s: s.login(YOUR_GMAIL, APP_PASSWORD); s.send_message(msg)
        print(f"[LOG] BLOGGER POSTED: {job['company']} | {job['loc']} | Batch:{job['batch']}")
        return True
    except Exception as e: print(f"BLOGGER FAIL {e}"); return False

def get_blog_url(job):
    time.sleep(80)
    try:
        r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=10", timeout=15)
        soup=BeautifulSoup(r.text,'xml')
        for item in soup.find_all('item'):
            if job['company'].split()[0].lower() in item.title.text.lower(): return item.find('link').text
        return soup.find('item').find('link').text
    except: return BLOG_URL

def post_telegram(job, url):
    text=f"""🔥 {job['company']} Off Campus Drive 2026

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
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHANNEL_ID, "text":text})
    print(f"[LOG] TELEGRAM: {job['company']} {job['loc']}")

jobs=fetch_only_hyd()
if not jobs: print("[LOG] No Hyd jobs found now - try after 1 hour"); exit()
for job in jobs:
    if is_posted(job['link']): continue
    if is_already_in_blog(job['company'], job['title']): save_link(job['link']); continue
    print(f"[LOG] Posting: {job['company']} | Loc:{job['loc']} | Batch:{job['batch']} | Qual:{job['qual']}")
    if post_blogger(job):
        url=get_blog_url(job)
        post_telegram(job, url)
        save_link(job['link'])
        print("[LOG] SUCCESS")
        break
