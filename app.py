from fastapi import FastAPI
from pydantic import BaseModel
from playwright.async_api import async_playwright
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# CORS MUST BE ADDED AFTER app IS CREATED
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExtractRequest(BaseModel):
    url: str

# Load Readability script
with open("Readability.js", "r", encoding="utf-8") as f:
    READABILITY_JS = f.read()

@app.post("/extract")
async def extract(payload: ExtractRequest):
    url = payload.url

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-infobars",
                "--disable-gpu",
                "--disable-features=IsolateOrigins,site-per-process"
            ]
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/118.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York",
            viewport={"width": 1280, "height": 800},
            device_scale_factor=1
        )
        
        page = await context.new_page()

        # ------------------------------------------
        # ⭐ FULL STEALTH PATCHES (Reuters-compatible)
        # ------------------------------------------

        # Remove navigator.webdriver flag
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # Fake chrome.runtime
        await page.add_init_script("""
            window.chrome = {
                runtime: {}
            };
        """)

        # Fake plugins
        await page.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [{ name: "Chrome PDF Viewer" }]
            });
        """)

        # Fake languages
        await page.add_init_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ["en-US", "en"]
            });
        """)

        # Fake permissions
        await page.add_init_script("""
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
        """)

        # ------------------------------------------
        # LOAD PAGE (Stealth)
        # ------------------------------------------
        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        except Exception as e:
            await browser.close()
            return {"error": f"Failed to load: {str(e)}"}

        # Give heavy sites time to hydrate (Reuters needs this)
        await page.wait_for_timeout(1500)

        # ------------------------------------------
        # Inject Readability
        # ------------------------------------------
        try:
            await page.add_script_tag(content=READABILITY_JS)
        except:
            await browser.close()
            return {"error": "Failed to inject Readability.js"}

        # ------------------------------------------
        # Extract readable content
        # ------------------------------------------
        article_text = await page.evaluate("""
            () => {
                try {
                    let article = new Readability(document).parse();
                    return article ? article.textContent : null;
                } catch (e) {
                    return null;
                }
            }
        """)

        await browser.close()

        if not article_text:
            return {"error": "Could not extract text"}

        return {"text": article_text}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
