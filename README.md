# Python Web Crawler (Basic & Advanced)

[Full technical guide can be found here 🕮](https://scrape.do/blog/web-crawler-python/)

This repository contains three Python scripts for web crawling:
- **simpleCrawler.py**: A minimal, educational web crawler for BFS crawling.
- **advancedCrawler.py**: A robust, multithreaded crawler with user-agent rotation, robots.txt compliance, and advanced filtering.
- **crawlerScrape-do.py**: A multithreaded crawler that leverages [Scrape.do](https://scrape.do) for anti-bot bypass and JavaScript rendering.

All scripts crawl public web pages, respect robots.txt, and export discovered URLs to CSV.

---

## Requirements

* Python 3.7+
* `requests` and `beautifulsoup4` libraries<br>Install with:

  ```bash
  pip install requests beautifulsoup4
  ```
* For `crawlerScrape-do.py`: a [Scrape.do API token](https://dashboard.scrape.do/signup) (**free** 1000 API credits/month)

---

## 🔍 How to Use Each Script

### `simpleCrawler.py`

**A minimal, educational web crawler using BFS.**

1. Set the seed URL and max pages (default: Wikipedia, 10 pages):
   ```python
   crawl("https://www.wikipedia.org/", max_pages=10)
   ```
2. Run:
   ```bash
   python simpleCrawler.py
   ```

Outputs crawled URLs to `crawled_urls.csv`.

---

### `advancedCrawler.py`

**A robust, multithreaded crawler with user-agent rotation, robots.txt compliance, and advanced filtering.**

1. Set the seed URL and max pages (default: Wikipedia, 20 pages):
   ```python
   threaded_crawl("https://www.wikipedia.org/", max_pages=20)
   ```
2. Run:
   ```bash
   python advancedCrawler.py
   ```

Features:
- Multithreading for speed
- User-agent rotation
- Logging to `crawler.log`
- Skips login/admin/cart/etc. pages
- Respects robots.txt
- Saves HTML to `pages/` and URLs to `crawled_urls.csv`

---

### `crawlerScrape-do.py`

**A multithreaded crawler that uses [Scrape.do](https://scrape.do) to bypass anti-bot protections and optionally render JavaScript.**

1. Set your Scrape.do API token and seed URL:
   ```python
   crawl_with_scrape_do(
       seed_url="https://en.wikipedia.org/",
       token="<your-scrape-do-token>",
       max_pages=10,
       delay=2.5,
       render=False
   )
   ```
2. Run:
   ```bash
   python crawlerScrape-do.py
   ```

Features:
- Uses Scrape.do for requests (handles proxies, CAPTCHAs, JS rendering)
- Multithreaded crawling
- Respects robots.txt
- Saves HTML to `pages_scrape_do/` and URLs to `crawled_urls_scrape_do.csv`
- Logging to `scrape_do_crawler.log`

---

## ⚠️ Legal & Ethical Notes

Please ensure:

* You crawl only **public web pages**
* You **do not automate excessive requests** or violate [website Terms of Service](https://policies.google.com/terms)
* Use Scrape.do responsibly and ethically

---

## 🚀 Why Use Scrape.do with `crawlerScrape-do.py`?

* Rotating premium proxies & geo-targeting
* Built-in header spoofing
* Handles redirects, CAPTCHAs, and JavaScript rendering
* 1000 free credits/month

👉 [Get your free API token here](https://dashboard.scrape.do/signup) 