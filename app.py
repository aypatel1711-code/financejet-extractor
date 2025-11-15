from fastapi import FastAPI
from pydantic import BaseModel
from playwright.async_api import async_playwright
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app = FastAPI()


class UrlInput(BaseModel):
    url: str

# Load Readability.js into memory
with open("Readability.js", "r", encoding="utf-8") as f:
    READABILITY_JS = f.read()


@app.post("/extract")
async def extract(payload: ExtractRequest):


    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )
        page = await browser.new_page()

        try:
            await page.goto(url, timeout=45000, wait_until="networkidle")
        except:
            await browser.close()
            return {"error": "Failed to load page"}

        # Inject readability script
        await page.add_script_tag(content=READABILITY_JS)

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
    uvicorn.run("app:app", host="0.0.0.0", port=10000)
