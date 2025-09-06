from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin

router = APIRouter(prefix="/api", tags=["scraper"])

BASE_URL = "https://quotes.toscrape.com/"
ROBOTS_URL = urljoin(BASE_URL, "robots.txt")

class Quote(BaseModel):
    text: str
    author: str
    tags: List[str]

class ScrapeResponse(BaseModel):
    source: str
    count: int
    data: List[Quote]

def allowed_by_robots(path: str) -> bool:
    rp = RobotFileParser()
    try:
        rp.set_url(ROBOTS_URL)
        rp.read()
    except Exception:
        # if robots can't be fetched, be conservative and deny
        return False
    return rp.can_fetch("*", urljoin(BASE_URL, path))

def fetch_quotes(tag: Optional[str] = None) -> List[Quote]:
    path = f"tag/{tag}/" if tag else ""
    if not allowed_by_robots(path):
        raise HTTPException(status_code=403, detail="Scraping disallowed by robots.txt")

    url = urljoin(BASE_URL, path)
    res = requests.get(url, timeout=10)
    if res.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Failed to fetch {url}: {res.status_code}")
    soup = BeautifulSoup(res.text, "html.parser")
    items = soup.select(".quote")
    quotes: List[Quote] = []
    for q in items:
        text_el = q.select_one(".text")
        author_el = q.select_one(".author")
        tag_els = q.select(".tags .tag")
        if not text_el or not author_el:
            continue
        quotes.append(Quote(
            text=text_el.get_text(strip=True).strip("“”"),
            author=author_el.get_text(strip=True),
            tags=[t.get_text(strip=True) for t in tag_els]
        ))
    return quotes

@router.get("/scrape", response_model=ScrapeResponse)
def scrape(tag: Optional[str] = Query(None, description="Optional tag to filter quotes")):
    data = fetch_quotes(tag=tag)
    return {"source": BASE_URL if not tag else urljoin(BASE_URL, f"tag/{tag}/"), "count": len(data), "data": data}
