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
    if "mba" in text: qual = "B.E/B.Tech/MBA/MCA"
    elif "bca" in text or "bsc" in text: qual = "B.E/B.Tech/B.Sc/BCA/MCA"
    else: qual = "B.E/B.Tech/M.Tech/MCA"
    years = re.findall(r'202[0-6]', text)
    batch = "/".join(sorted(list(set(years)))[:4]) if years else "2024/2025/2026"
    if "0-1" in text or "fresher" in text: exp = "Freshers (0-1 Year)"
    elif "1-2 year" in text: exp = "0-2 Years"
    else: exp = "Freshers"
    if "hyderabad" in text and "remote" in text: loc = "Remote / Hyderabad"
    elif "hyderabad" in text: loc = "Hyderabad"
    elif "remote" in text: loc = "Remote / Hyderabad"
    else: loc = "Remote (India) - Hyd Eligible"
    return qual, batch, exp, loc

def fetch_only_hyd():
    jobs=[]
    print("[LOG] Fetching real jobs...")
    try:
        r=requests.get("https://jobicy.com/api/v2/remote-jobs?count=50&geo=india", timeout=20).json()
        all_jobs=r.get('jobs',[])
        print(f"[LOG] Jobicy total API: {len(all_jobs)}")
        for j in all_jobs[:20]:
            title=j.get('jobTitle',''); desc=j.get('jobDescription',''); company=j.get('companyName','')
            if any(x in title.lower() for x in ["für","ä","ö","ß"]): continue
            qual,batch,exp,loc = parse_dynamic(desc, title)
            jobs.append({"title":title[:70],"company":company,"link":j['url'],"desc":desc[:800],"qual":qual,"batch":batch,"exp":exp,"loc":loc,"source":"Jobicy"})
        print(f"[LOG] Jobicy after filter: {len(jobs)}")
    except Exception as e: print(f"Jobicy fail {e}")

    try:
        print("[LOG] Trying Remotive...")
        r=requests.get("https://remotive.com/api/remote-jobs?limit=50", timeout=20).json()
        c=0
        for j in r['jobs']:
            if any(x in j['title'].lower() for x in ["für","ä","ö","ß"]): continue
            qual,batch,exp,loc = parse_dynamic(j['description'], j['title'])
            jobs.append({"title":j['title'][:70],"company":j['company_name'],"link":j['url'],"desc":j['description'][:800],"qual":qual,"batch":batch,"exp":exp,"loc":loc,"source":"Remotive"})
            c+=1
            if c>=5: break
        print(f"[LOG] Remotive added: {c} | Total: {len(jobs)}")
    except Exception as e: print(f"Remotive fail {e}")

    try:
        print("[LOG] Trying ArbeitNow...")
        r=requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=20).json()
        c=0
        for j in r['data'][:20]:
            full=(j.get('title','')+j.get('description','')).lower()
            if "india" in full or "remote" in full or "hyderabad" in full:
                qual,batch,exp,loc = parse_dynamic(j.get('description',''), j.get('title',''))
                jobs.append({"title":j.get('title','')[:70],"company":j.get('company_name','Company'),"link":j.get('url',''),"desc":j.get('description','')[:800],"qual":qual,"batch":batch,"exp":exp,"loc":loc,"source":"ArbeitNow"})
                c+=1
                if c>=3: break
        print(f"[LOG] ArbeitNow added: {c} | Total: {len(jobs)}")
    except Exception as e: print(f"ArbeitNow fail {e}")

    random.shuffle(jobs)
    print(f"[LOG] TOTAL READY: {len(jobs)}")
    for j in jobs[:5]: print(f"[LOG] -> {j['source']} | {j['company']} | {j['loc']} | {j['batch']}")
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
    uid=random.randint(10000,99999)
    now=datetime.now().strftime("%Y%m%d%H%M")
    job['uid']=str(uid)
    html=f"""<div style="font-family:Arial;line-height:1.8;"><h1>{job['company']} Hiring {job['title']} - {job['loc']} {now}</h1><p><b>Hyd Real Job:</b> {job['company']} hiring {job['title']} in {job['loc']}.</p><div style="background:#eef2ff;padding:15px;border-radius:8px;"><p>💼 Job Role: {job['title']}<br>🏢 Company: {job['company']}<br>🎓 Qualification: {job['qual']}<br>🔹 Batch: {job['batch']}<br>🆕 Experience: {job['exp']}<br>📍 Location: {job['loc']}</p></div><p>{job['desc'][:900]}</p><div style="text-align:center;margin:25px;"><a href="{job['link']}" style="background:#0d6efd;color:#fff;padding:16px 45px;text-decoration:none;border-radius:8px;font-weight:bold;">🌐 Apply Here</a></div></div>"""
    msg=MIMEText(html,"html")
    msg['Subject']=f"{job['company']} {job['title']} {job['loc']} {uid} {now}"
    msg['From']=YOUR_GMAIL; msg['To']=BLOGGER_EMAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as s: s.login(YOUR_GMAIL, APP_PASSWORD); s.send_message(msg)
        print(f"[LOG] BLOGGER SENT UID:{uid} - {job['company']}")
        return True
    except Exception as e: print(f"BLOGGER FAIL {e}"); return False

def get_blog_url(job):
    uid=job.get('uid','')
    print(f"[LOG] Searching UID {uid} in RSS - 4 mins wait")
    for attempt in range(8):
        time.sleep(30)
        try:
            r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=20", timeout=20)
            soup=BeautifulSoup(r.text,'xml')
            for item in soup.find_all('item'):
                if uid in item.title.text:
                    link=item.find('link').text
                    print(f"[LOG] CORRECT URL FOUND: {link}")
                    return link
            print(f"[LOG] Attempt {attempt+1} - UID not yet, latest: {soup.find('item').title.text[:40] if soup.find('item') else 'none'}")
        except Exception as e: print(f"RSS fail {e}")
    print("[LOG] Fallback latest URL")
    try:
        r=requests.get(f"{BLOG_URL}/feeds/posts/default?alt=rss&max-results=1", timeout=15)
        soup=BeautifulSoup(r.text,'xml')
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
    print(f"[LOG] TELEGRAM DONE: {url}")

jobs=fetch_only_hyd()
if not jobs: print("[LOG] No jobs today - retry after 2 hours"); exit()
for job in jobs:
    if is_posted(job['link']): continue
    if is_already_in_blog(job['company'], job['title']): save_link(job['link']); continue
    if post_blogger(job):
        url=get_blog_url(job)
        post_telegram(job, url)
        save_link(job['link'])
        print("[LOG] SUCCESS DONE")
        break
