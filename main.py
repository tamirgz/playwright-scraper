from fastapi import FastAPI, Query
from playwright.async_api import async_playwright
import asyncio

app = FastAPI()

@app.get("/scrape")
async def scrape(url: str = Query(...)):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=60000)  # 60 seconds timeout
            html_content = await page.content()
            await browser.close()
            return {"url": url, "html": html_content}
    except Exception as e:
        return {"error": str(e)}
