from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright
from readability import Document
import uvicorn
import os

app = FastAPI()

# ----------------------------
# CORS (VERY IMPORTANT)
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

class ExtractRequest(BaseModel):
    url: str


@app.get("/")
def home():
    return {"message": "Extractor is running."}


@app.post("/extract")
async def extract(payload: ExtractRequest):
    url = payload.url.strip()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )
        page = await browser.new_page()

        try:
            await page.goto(url, timeout=55000, wait_until="domcontentloaded")
        except Exception as e:
            await browser.close()
            return {"error": f"Failed to load page: {e}"}

        # 🔥 Get raw HTML safely — NO script injection
        try:
            html = await page.content()
        except Exception as e:
            await browser.close()
            return {"error": f"Failed to read HTML: {e}"}

        await browser.close()

    # 🔥 Use Python Readability — immune to CSP
    try:
        doc = Document(html)
        text = doc.text()
    except Exception as e:
        return {"error": f"Readability failed: {e}"}

    if not text or len(text.strip()) < 50:
        return {"error": "Could not extract article text"}

    return {"text": text}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)

