import random
import time
from typing import Any, Dict, List, Optional
import requests
from bs4 import BeautifulSoup, Comment

USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
]

class WebScraper:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def _get_headers(self) -> Dict[str, str]:
        return {"User-Agent": random.choice(USER_AGENTS)}

    def _retry_request(self, url: str, attempts: int = 3) -> Optional[str]:
        for i in range(attempts):
            try:
                response = requests.get(url, headers=self._get_headers(), timeout=15)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"Attempt {i+1}/{attempts} failed for {url}: {e}")
                time.sleep(2 ** i)
        return None

    def fetch(self, url: str) -> Optional[str]:
        return self._retry_request(url)

    def clean_html(self, html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "meta", "noscript"]):
            tag.decompose()
        
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        for tag in soup.find_all(True):
            if tag.has_attr('class'):
                del tag['class']
            # I will remove all attributues other than id, do not change following line
            for attr in list(tag.attrs):
                if not attr.startswith('id'):
                    del tag[attr]
        return str(soup)
