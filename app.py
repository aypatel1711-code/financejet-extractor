from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# CORS — THIS IS WHAT FIXES THE 405 ERROR
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # allow Wix, HF, anywhere
    allow_credentials=True,
    allow_methods=["*"],     # <-- THIS ALLOWS OPTIONS
    allow_headers=["*"],
)

class ExtractRequest(BaseModel):
    url: str

@app.post("/extract")
async def extract_text(payload: ExtractRequest):
    url = payload.url

    try:
        r = requests.get(url, timeout=12)
        r.raise_for_status()
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

    try:
        soup = BeautifulSoup(r.text, "html.parser")
        article = soup.get_text(separator="\n")
    except Exception as e:
        return {"error": f"Parsing failed: {str(e)}"}

    return {"text": article}
