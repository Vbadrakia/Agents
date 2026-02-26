import requests
from bs4 import BeautifulSoup
from utils_memory import is_duplicate

KEYWORDS = ["Rajkot", "Gujarat", "Remote"]

def get_job_updates():
    url = "https://in.indeed.com/jobs?q=salesforce+developer&l=India"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    job_cards = soup.find_all("a")

    jobs = []

    for job in job_cards:
        title = job.text.strip()

        if any(keyword.lower() in title.lower() for keyword in KEYWORDS):
            link = "https://in.indeed.com" + job.get("href", "")
            if not is_duplicate("jobs", link):
                jobs.append(f"- {title}\n{link}")

    if not jobs:
        return "💼 No new Rajkot/Remote jobs."

    return "💼 Filtered Jobs:\n\n" + "\n\n".join(jobs[:5])
