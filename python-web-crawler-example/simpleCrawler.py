import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import csv
import urllib.robotparser


# Skip files with non-HTML extensions (e.g., images, videos, PDFs)
def should_skip_url(url):
    skip_extensions = (
        ".xml", ".json", ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg",
        ".zip", ".rar", ".mp4", ".mp3", ".ico"
    )
    return url.lower().endswith(skip_extensions)


# Download and return HTML content from a URL, if valid and accessible
def fetch(url):
    try:
        response = requests.get(url, timeout=5, headers={"User-Agent": "MyCrawler"})
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            if "html" in content_type:
                return response.text
    except requests.RequestException:
        pass  # Silently skip fetch errors
    return ""


# Extract same-domain and subdomain links from a given HTML page
def extract_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    base_parsed = urlparse(base_url)
    base_domain = ".".join(base_parsed.netloc.split(".")[-2:])  # e.g., wikipedia.org

    links = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)

        # Keep only links from the same base domain (e.g., *.wikipedia.org)
        if parsed.netloc.endswith(base_domain) and absolute.startswith("http"):
            links.add(absolute)

    return links


# Check if the URL is allowed by robots.txt, fallback=True means assume allowed if inaccessible
def is_allowed(url, user_agent="MyCrawler", fallback=True):
    rp = urllib.robotparser.RobotFileParser()
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except:
        print(f"[robots.txt not accessible] Proceeding with: {url}")
        return fallback


# Main crawl logic: BFS over discovered links, obeying robots.txt and skipping unwanted file types
def crawl(seed_url, max_pages=10):
    visited = set()                  # Track visited URLs
    queue = deque([seed_url])        # Queue for URLs to visit (BFS)
    user_agent = "MyCrawler"         # User-Agent string for headers and robots.txt

    while queue and len(visited) < max_pages:
        url = queue.popleft()

        # Skip already visited, disallowed, or unwanted file types
        if (
            url in visited or
            should_skip_url(url) or
            not is_allowed(url, user_agent)
        ):
            continue

        print(f"Crawling: {url}")
        html = fetch(url)
        if not html:
            continue

        # Extract links and add new ones to the queue
        links = extract_links(html, url)
        queue.extend(links - visited)
        visited.add(url)

    # Export crawled URLs to a CSV file
    with open("crawled_urls.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["URL"])
        for url in visited:
            writer.writerow([url])


# Start crawling from the Wikipedia homepage
crawl("https://www.wikipedia.org/", max_pages=10)
