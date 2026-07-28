import requests, json, os, smtplib, random
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
import time
from datetime import datetime

# --- NEE 5 DETAILS IKKADA ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8978732819:AAElHZKLxERyG9b0psFdyV33C8lUcN-fACo")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "-1003973586076")
YOUR_GMAIL = os.environ.get("YOUR_GMAIL", "satishkasarla206@gmail.com")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "mzcw ylvz cmol cgqk")
BLOGGER_EMAIL = os.environ.get("BLOGGER_EMAIL", "satishkasarla206.hydhirehub123@blogger.com")

# --- 1. INTERNSHALA ---
def get_internshala():
    jobs = []
    try:
        url = "https://internshala.com/jobs/jobs-in-hyderabad/"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, 'lxml')
        for card in soup.select('.individual_internship_details')[:3]:
            try:
                title = card.select_one('.job-internship-name').text.strip()
                company = card.select_one('.company-name').text.strip()
                link = "https://internshala.com" + card.select_one('a.job-title-href')['href']
                jobs.append({"title": f"{title}", "company": company, "link": link, "source": "Internshala"})
            except: continue
    except Exception as e: print("Internshala error", e)
    return jobs

# --- 2. APNA JOBS (Hyderabad) ---
def get_apna():
    jobs = []
    try:
        url = "https://apna.co/jobs-in-hyderabad"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, 'lxml')
        for card in soup.select('div[data-testid="job-card"]')[:3]:
            try:
                title = card.select_one('h2').text.strip()
                company = "Top Company"
                link = "https://apna.co" + card.find('a')['href'] if card.find('a') else "https://apna.co/jobs-in-hyderabad"
                jobs.append({"title": title, "company": company, "link": link, "source": "Apna.co"})
            except: continue
    except Exception as e: print("Apna error", e)
    return jobs

# --- 3. INDEED RSS (Most Stable) ---
def get_indeed():
    jobs = []
    try:
        # Indeed RSS is very stable for automation
        url = "https://rss.indeed.com/rss?q=fresher&l=Hyderabad"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, 'lxml')
        for item in soup.find_all('item')[:3]:
            try:
                title = item.title.text.strip()
                link = item.link.text.strip()
                jobs.append({"title": title, "company": "Indeed Job", "link": link, "source": "Indeed"})
            except: continue
    except Exception as e: print("Indeed error", e)
    return jobs

# --- 4. REMOTIVE / REMOTE OK (IT Jobs kosam) ---
def get_remoteok():
    jobs = []
    try:
        url = "https://remoteok.com/remote-jobs-rss"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, 'lxml')
        for item in soup.find_all('item')[:2]:
            try:
                title = item.title.text.strip()
                link = item.link.text.strip()
                if "developer" in title.lower() or "fresher" in title.lower():
                    jobs.append({"title": title, "company": "Remote Company", "link": link, "source": "RemoteOK"})
            except: continue
    except: pass
    return jobs

def is_posted(link):
    try:
        with open('posted.json','r') as f: return link in json.load(f)
    except: return False

def save_link(link):
    data = []
    if os.path.exists('posted.json'):
        try:
            with open('posted.json','r') as f: data = json.load(f)
        except: pass
    data.append(link)
    # Last 100 links mathrame save chesta, file pedda kakunda
    data = data[-100:]
    with open('posted.json','w') as f: json.dump(data,f)

def post_telegram(job):
    text = f"🚨 <b>{job['title']}</b>\n\n🏢 Company: {job['company']}\n📍 Hyderabad\n🔗 Source: {job['source']}\n\n👉 Apply Now: {job['link']}\n\n#HyderabadJobs #{job['source']} #Freshers"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False})

def post_blogger(job):
    desc = f"<p><b>Company:</b> {job['company']}</p><p><b>Location:</b> Hyderabad</p><p><b>Source:</b> {job['source']}</p><p><b>My Take:</b> Ee {job['title']} role {job['company']} lo Hyderabad freshers ki super chance. Immediate ga apply cheyandi, competition thakkuva undi ippudu.</p><p><b>Apply Link:</b> <a href='{job['link']}'>{job['link']}</a></p>"
    html = f"<h2>{job['title']} at {job['company']} - Hyderabad | {job['source']}</h2>{desc}"
    msg = MIMEText(html, "html")
    msg['Subject'] = f"{job['title']} at {job['company']} - Hyderabad Jobs 2026"
    msg['From'] = YOUR_GMAIL
    msg['To'] = BLOGGER_EMAIL
    with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
        s.login(YOUR_GMAIL, APP_PASSWORD)
        s.send_message(msg)
    print(f"Posted: {job['title']} from {job['source']}")

# --- MAIN RUNNER ---
all_jobs = []
all_jobs.extend(get_internshala())
all_jobs.extend(get_apna())
all_jobs.extend(get_indeed())
all_jobs.extend(get_remoteok())

random.shuffle(all_jobs) # Prathi sari different portal nundi vachela

posted_count = 0
for job in all_jobs:
    if not is_posted(job['link']):
        if posted_count >= 2: # Oka sari ki 2 jobs mathrame, spam kakunda
            break
        post_telegram(job)
        post_blogger(job)
        save_link(job['link'])
        posted_count += 1
        time.sleep(8)

print(f"Done. {posted_count} new jobs posted at {datetime.now()}")
