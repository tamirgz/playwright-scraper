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
            await page.goto(url)
            content = await page.title()
            await browser.close()
            return {"url": url, "title": content}
    except Exception as e:
        return {"error": str(e)}
