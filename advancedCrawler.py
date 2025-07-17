import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import csv
import urllib.robotparser
from concurrent.futures import ThreadPoolExecutor
import time
import random
import logging
import hashlib
import os

# Setup logging to track crawl progress and errors
logging.basicConfig(
    filename="crawler.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Pool of realistic user agents for rotating headers
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/15.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/113.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1"
]

# Proxy list placeholder — uncomment if needed
PROXIES = [
    # "http://proxy1.example.com:8000",
    # "http://proxy2.example.com:8080",
]

# URLs containing these paths or query patterns will be skipped
EXCLUDED_PATHS = ["/login", "/admin", "/signup", "/cart", "/checkout"]
EXCLUDED_QUERY_PARAMS = ["q=", "search=", "filter="]


# File extensions to skip when identifying links
def should_skip_url(url):
    skip_extensions = (
        ".xml", ".json", ".pdf", ".jpg", ".jpeg", ".png", ".gif",
        ".svg", ".zip", ".rar", ".mp4", ".mp3", ".ico"
    )
    return url.lower().endswith(skip_extensions)


# Send HTTP request with retry and randomized user-agent; return HTML only
def fetch(url, max_retries=3):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }

    # To use proxies, uncomment this
    # proxies = {"http": random.choice(PROXIES), "https": random.choice(PROXIES)}

    for attempt in range(max_retries):
        try:
            response = requests.get(
                url,
                timeout=5,
                headers=headers,
                # proxies=proxies
            )
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                if "html" in content_type:
                    return response.text
            break  # break if non-200 response
        except requests.RequestException as e:
            logging.warning(f"[retry {attempt + 1}] Error fetching {url}: {e}")
            time.sleep(1.5 + attempt * 1.0)  # simple linear backoff
    return ""


# Extract valid internal/subdomain links from HTML content
def extract_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    base_parsed = urlparse(base_url)
    base_domain = base_parsed.netloc
    base_root = ".".join(base_domain.split(".")[-2:])  # e.g. wikipedia.org

    links = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)

        # Only allow same base domain (e.g. *.wikipedia.org)
        if ".".join(parsed.netloc.split(".")[-2:]) != base_root:
            continue
        if any(path in parsed.path for path in EXCLUDED_PATHS):
            continue
        if any(q in parsed.query for q in EXCLUDED_QUERY_PARAMS):
            continue
        if absolute.startswith("http"):
            links.add(absolute)

    return links


# Check robots.txt rules for the URL; return True if allowed
def is_allowed(url, user_agent="MyCrawler"):
    rp = urllib.robotparser.RobotFileParser()
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except:
        return False  # conservative fallback


# Save HTML content to disk using hashed filename
def save_page(html, url, folder="pages"):
    os.makedirs(folder, exist_ok=True)
    file_id = hashlib.md5(url.encode()).hexdigest()
    filepath = os.path.join(folder, f"{file_id}.html")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)


# Multithreaded crawler core loop
def threaded_crawl(seed_url, max_pages=50, max_workers=5, delay_range=(1.5, 3.5)):
    visited = set()
    queue = deque([seed_url])

    def worker(url):
        if (
            url in visited or
            should_skip_url(url) or
            not is_allowed(url)
        ):
            return []

        logging.info(f"Crawling: {url}")
        html = fetch(url)

        time.sleep(random.uniform(*delay_range))  # throttle to reduce pressure

        if not html:
            return []

        save_page(html, url)
        visited.add(url)
        return extract_links(html, url)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        while queue and len(visited) < max_pages:
            batch = []
            while queue and len(batch) < max_workers:
                batch.append(queue.popleft())

            futures = [executor.submit(worker, url) for url in batch]
            for future in futures:
                try:
                    links = future.result()
                    queue.extend(link for link in links if link not in visited)
                except Exception as e:
                    logging.error(f"Worker failure: {e}")

    # Save the list of visited URLs to CSV
    with open("crawled_urls.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["URL"])
        for url in visited:
            writer.writerow([url])


# Start the crawler from Wikipedia's homepage
threaded_crawl("https://www.wikipedia.org/", max_pages=20)
