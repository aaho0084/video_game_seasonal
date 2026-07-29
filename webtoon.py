import logging
from typing import List, Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WebtoonAPI")


class WebtoonAPI:
    """Client wrapper for the Korea Webtoon API.
    
    Supports fetching webtoons from Naver, Kakao, and KakaoPage,
    as well as searching by keyword or filtering by release schedule.
    """
    
    BASE_URL = "https://korea-webtoon-api-cc312a203ae0.herokuapp.com"
    VALID_PROVIDERS = {"naver", "kakao", "kakaopage"}
    VALID_DAYS = {"mon", "tue", "wed", "thu", "fri", "sat", "sun", "finished"}

    def __init__(self, timeout: int = 12, max_retries: int = 3):
        """Initialize the API client with session retry logic."""
        self.timeout = timeout
        self.session = requests.Session()
        
        # Exponential backoff retry strategy for flaky connections & rate limits
        retries = Retry(
            total=max_retries,
            backoff_factor=2.0,  # Delays: 2s, 4s, 8s
            status_forcelist=[403, 429, 500, 502, 503, 504],
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })

    def get_webtoons(
        self, 
        provider: str = "naver", 
        update_day: str = "mon", 
        page: int = 1, 
        per_page: int = 50
    ) -> List[Dict[str, Any]]:
        """Fetch a list of webtoons for a given provider and schedule day."""
        provider = provider.lower()
        update_day = update_day.lower()

        if provider not in self.VALID_PROVIDERS:
            raise ValueError(f"Invalid provider '{provider}'. Must be one of: {self.VALID_PROVIDERS}")
        
        if update_day not in self.VALID_DAYS:
            raise ValueError(f"Invalid update_day '{update_day}'. Must be one of: {self.VALID_DAYS}")

        params = {
            "provider": provider,
            "updateDay": update_day,
            "page": page,
            "perPage": per_page
        }

        try:
            response = self.session.get(f"{self.BASE_URL}/webtoons", params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("webtoons", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch webtoons ({provider}/{update_day}): {e}")
            return []

    def search_webtoons(self, keyword: str) -> List[Dict[str, Any]]:
        """Search for webtoons by title or author across platforms."""
        if not keyword or not keyword.strip():
            return []

        params = {"keyword": keyword.strip()}

        try:
            response = self.session.get(f"{self.BASE_URL}/search", params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("webtoons", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Search request failed for keyword '{keyword}': {e}")
            return []