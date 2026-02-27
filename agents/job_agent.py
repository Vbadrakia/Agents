import requests
from bs4 import BeautifulSoup

def get_job_updates():
    """Fetches job listings for Rajkot/Remote positions."""
    keywords = ["python developer", "AI engineer", "data analyst"]
    location = "Rajkot"
    jobs = []

    for keyword in keywords:
        try:
            url = f"https://www.google.com/search?q={keyword}+jobs+in+{location}+OR+remote&ibp=htl;jobs"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            for item in soup.find_all("div", class_="BjJfJf")[:2]:
                title = item.get_text(strip=True)
                if title and title not in jobs:
                    jobs.append(title)
        except Exception as e:
            print(f"Error fetching jobs for {keyword}: {e}")
            continue

    if jobs:
        job_text = "\n".join([f"• {job}" for job in jobs[:5]])
        return f"💼 Job Updates (Rajkot/Remote)\n\n{job_text}"
    else:
        return "💼 No new Rajkot/Remote jobs."
