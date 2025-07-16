import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import csv
import urllib.robotparser
from concurrent.futures import ThreadPoolExecutor
import time
import logging
import hashlib
import os


# Set up logging to track progress and issues
logging.basicConfig(
    filename="scrape_do_crawler.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


# Config: filters to skip certain paths, query params, and file extensions
EXCLUDED_PATHS = ["/login", "/signup", "/cart", "/checkout"]
EXCLUDED_QUERY_PARAMS = ["q=", "search=", "filter="]
SKIP_EXTENSIONS = (
    ".xml", ".json", ".pdf", ".jpg", ".jpeg", ".png", ".gif",
    ".svg", ".zip", ".rar", ".mp4", ".mp3", ".ico"
)


def should_skip_url(url):
    """Skip links that point to static files or undesired formats."""
    return url.lower().endswith(SKIP_EXTENSIONS)


def fetch(url, token, render=False):
    """
    Request a URL through Scrape.do. Returns HTML if successful.
    Optionally enables JavaScript rendering with `render=True`.
    """
    api_url = "https://api.scrape.do"
    params = {
        "token": token,
        "url": url
    }
    if render:
        params["render"] = "true"

    try:
        response = requests.get(api_url, params=params, timeout=10)
        if response.status_code == 200:
            return response.text
    except requests.RequestException as e:
        logging.warning(f"[Scrape.do fetch failed] {url} -> {e}")
    return ""


def extract_links(html, base_url):
    """
    Extracts valid, same-domain or subdomain links from a page.
    Filters out paths and query strings you don't want to crawl.
    """
    soup = BeautifulSoup(html, "html.parser")
    base_domain = ".".join(urlparse(base_url).netloc.split(".")[-2:])  # e.g., wikipedia.org
    links = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)

        if not parsed.netloc.endswith(base_domain):
            continue
        if any(path in parsed.path for path in EXCLUDED_PATHS):
            continue
        if any(q in parsed.query for q in EXCLUDED_QUERY_PARAMS):
            continue
        if absolute.startswith("http"):
            links.add(absolute)

    return links


def is_allowed(url, user_agent="Mozilla/5.0", fallback=True):
    """
    Check if the given URL is allowed by robots.txt.
    If robots.txt is unreachable, return `fallback`.
    """
    rp = urllib.robotparser.RobotFileParser()
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        logging.warning(f"[robots.txt inaccessible] {url} – falling back to {fallback}")
        return fallback


def save_page(html, url, folder="pages_scrape_do"):
    """
    Save HTML content to disk using an MD5 hash of the URL for the filename.
    """
    os.makedirs(folder, exist_ok=True)
    file_id = hashlib.md5(url.encode()).hexdigest()
    filepath = os.path.join(folder, f"{file_id}.html")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)


def crawl_with_scrape_do(seed_url, token, max_pages=50, max_workers=5, delay=2.0, render=False):
    """
    Multithreaded crawler that uses Scrape.do for fetching.
    Respects robots.txt, saves pages, and writes visited URLs to CSV.
    """
    visited = set()
    queue = deque([seed_url])
    user_agent = "Mozilla/5.0"

    def worker(url):
        if (
            url in visited or
            should_skip_url(url) or
            not is_allowed(url, user_agent)
        ):
            return []

        logging.info(f"Crawling via Scrape.do: {url}")
        html = fetch(url, token=token, render=render)
        time.sleep(delay)  # Respectful delay between requests

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
                    logging.error(f"[Worker error] {e}")

    # Export crawled URLs to a CSV file
    with open("crawled_urls_scrape_do.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["URL"])
        for url in visited:
            writer.writerow([url])


# Run the crawler with your Scrape.do token
crawl_with_scrape_do(
    seed_url="https://en.wikipedia.org/",
    token="94d5e4ba4e4f4466949e88b62b2539968b826d3248e",
    max_pages=10,
    delay=2.5,
    render=False
)
