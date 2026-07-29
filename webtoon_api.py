import logging
from typing import List, Dict, Any
import requests
import pandas as pd
import streamlit as st

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WebtoonApp")

# ==========================================
# 1. DIRECT API FETCHER (NO HEROKU NEEDED)
# ==========================================
class DirectWebtoonFetcher:
    """Fetches webtoon metadata directly from official endpoints."""
    
    NAV_URL = "https://comic.naver.com/api/article/list/weekday"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://comic.naver.com/webtoon"
    }

    DAY_MAP = {
        "mon": "MONDAY", "tue": "TUESDAY", "wed": "WEDNESDAY",
        "thu": "THURSDAY", "fri": "FRIDAY", "sat": "SATURDAY",
        "sun": "SUNDAY"
    }

    @classmethod
    def fetch_naver(cls, day: str = "mon") -> List[Dict[str, Any]]:
        mapped_day = cls.DAY_MAP.get(day.lower(), "MONDAY")
        params = {"week": mapped_day.lower()}
        
        try:
            res = requests.get(cls.NAV_URL, params=params, headers=cls.HEADERS, timeout=8)
            res.raise_for_status()
            data = res.json()
            
            raw_titles = data.get("titleList", [])
            formatted = []
            
            for item in raw_titles:
                authors = [a.get("name") for a in item.get("communityArtists", [])]
                author_str = ", ".join(authors) if authors else "Unknown"
                
                title_id = item.get("titleId")
                formatted.append({
                    "title": item.get("titleName", "Untitled"),
                    "author": author_str,
                    "thumbnail": item.get("thumbnailUrl"),
                    "url": f"https://comic.naver.com/webtoon/list?titleId={title_id}",
                    "provider": "naver",
                    "isUpdated": item.get("up", False)
                })
            return formatted
            
        except Exception as e:
            logger.warning(f"Direct Naver fetch failed: {e}")
            return []


# Offline Fallback Dataset if cloud outbound traffic is throttled
MOCK_WEBTOONS = [
    {
        "title": "Tower of God",
        "author": "SIU",
        "thumbnail": "https://image-comic.pstatic.net/webtoon/183559/thumbnail/thumbnail_IMAG21_3137538258352391264.jpg",
        "url": "https://comic.naver.com/webtoon/list?titleId=183559",
        "provider": "naver",
        "isUpdated": False
    },
    {
        "title": "The Remarried Empress",
        "author": "Alphatart, Sumpul",
        "thumbnail": "https://image-comic.pstatic.net/webtoon/735661/thumbnail/thumbnail_IMAG21_3862215456209823616.jpg",
        "url": "https://comic.naver.com/webtoon/list?titleId=735661",
        "provider": "naver",
        "isUpdated": True
    },
    {
        "title": "Omniscient Reader",
        "author": "singNsong, Sleepy-C",
        "thumbnail": "https://image-comic.pstatic.net/webtoon/747269/thumbnail/thumbnail_IMAG21_3871146816041183173.jpg",
        "url": "https://comic.naver.com/webtoon/list?titleId=747269",
        "provider": "naver",
        "isUpdated": True
    }
]


# ==========================================
# 2. STREAMLIT APP LOGIC
# ==========================================
st.set_page_config(page_title="Korea Webtoon Explorer", page_icon="💚", layout="wide")

st.title("💚 Korean Webtoon Explorer")
st.write("Real-time rankings and schedules deployed on Streamlit Cloud.")

# Sidebar Controls
with st.sidebar:
    st.header("Search & Filters")
    provider = st.selectbox("Platform", options=["naver"])
    update_day = st.selectbox(
        "Release Day", 
        options=["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    )
    search_query = st.text_input("Search Title or Author")
    item_limit = st.slider("Display Limit", 4, 40, 16)


# Cache API calls for 15 minutes to stay within Cloud rate limits
@st.cache_data(ttl=900, show_spinner="Connecting to webtoon services...")
def load_data(platform: str, day: str):
    if platform == "naver":
        results = DirectWebtoonFetcher.fetch_naver(day=day)
        if results:
            return results, "Live API"
            
    return MOCK_WEBTOONS, "Fallback Dataset"


webtoon_list, source_type = load_data(provider, update_day)

# Filter by Search Query if provided
if search_query.strip():
    q = search_query.lower()
    webtoon_list = [
        w for w in webtoon_list 
        if q in w.get("title", "").lower() or q in w.get("author", "").lower()
    ]

# Status Indicator Banner
if source_type == "Live API":
    st.success(f"🟢 Connected directly to Naver Webtoon ({len(webtoon_list)} titles loaded)")
else:
    st.info("🟡 Gateway response restricted. Displaying cached webtoon dataset.")

# Grid Display
if webtoon_list:
    items = webtoon_list[:item_limit]
    cols = st.columns(4)
    
    for idx, item in enumerate(items):
        with cols[idx % 4]:
            st.markdown(f"#### #{idx + 1} {item.get('title')}")
            
            thumb = item.get("thumbnail")
            if thumb:
                try:
                    st.image(thumb, use_container_width=True)
                except Exception:
                    st.caption("🖼️ (Image restricted by host CDN)")

            st.caption(f"✍️ **Author:** {item.get('author')}")
            if item.get("isUpdated"):
                st.markdown("🔥 **New Episode Today!**")
            st.markdown(f"[📖 Read Webtoon]({item.get('url')})")
            st.divider()

    with st.expander("📊 View Data Table"):
        st.dataframe(pd.DataFrame(webtoon_list), use_container_width=True)