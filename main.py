from fastapi import FastAPI, Query
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import asyncio

app = FastAPI()

@app.get("/scrape")
async def scrape(url: str = Query(...)):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=300000)  # 120 seconds timeout
            html_content = await page.content()
            await browser.close()
            return {"url": url, "html": html_content}
    except Exception as e:
        return {"error": str(e)}

@app.get("/crawl")
async def crawl(
    url: str = Query(..., description="Starting URL"),
    max_depth: int = Query(2, description="Maximum crawl depth"),
    max_pages: int = Query(20, description="Maximum pages to crawl")
):
    visited = set()
    results = []

    async def scrape_page(page, current_url):
        await page.goto(current_url, wait_until="networkidle", timeout=300000)
        html = await page.content()
        title = await page.title()

        # Parse with BeautifulSoup to get meta description
        soup = BeautifulSoup(html, "html.parser")
        meta_desc = soup.find("meta", attrs={"name": "description"})
        meta_description = meta_desc["content"] if meta_desc and "content" in meta_desc.attrs else ""

        # Extract internal links
        anchors = await page.eval_on_selector_all("a[href]", "els => els.map(el => el.href)")
        parsed_base = urlparse(url)
        internal_links = set()

        for link in anchors:
            parsed_link = urlparse(link)
            if not parsed_link.netloc or parsed_link.netloc == parsed_base.netloc:
                full_link = urljoin(current_url, parsed_link.path)
                if full_link not in visited:
                    internal_links.add(full_link)

        return {
            "url": current_url,
            "title": title,
            "meta_description": meta_description,
            "internal_links": list(internal_links),
            "html": html
        }, internal_links

    async def crawl_recursive(page, current_url, depth):
        if current_url in visited or len(visited) >= max_pages or depth > max_depth:
            return
        visited.add(current_url)

        try:
            data, internal_links = await scrape_page(page, current_url)
            results.append(data)
            for link in internal_links:
                if len(visited) >= max_pages:
                    break
                await crawl_recursive(page, link, depth + 1)
        except Exception as e:
            results.append({"url": current_url, "error": str(e)})

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await crawl_recursive(page, url, depth=0)
        await browser.close()

    return {
        "start_url": url,
        "pages_crawled": len(visited),
        "results": results
    }
