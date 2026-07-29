import logging
from typing import List, Dict, Any
from datetime import datetime
import requests
import pandas as pd
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WebtoonApp")

# ==========================================
# 1. DIRECT NAVER FETCHING LOGIC
# ==========================================
class DirectWebtoonFetcher:
    """Fetches real-time webtoon rankings directly from Naver API."""
    
    NAV_URL = "https://comic.naver.com/api/article/list/weekday"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://comic.naver.com/webtoon"
    }

    DAY_MAP = {
        0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"
    }

    @classmethod
    def get_current_day_code(cls) -> str:
        """Returns today's day string based on current server weekday."""
        weekday_num = datetime.now().weekday()
        return cls.DAY_MAP.get(weekday_num, "wed")

    @classmethod
    def fetch_top_webtoons(cls, day: str, limit: int = 10) -> List[Dict[str, Any]]:
        params = {"week": day.lower()}
        
        try:
            res = requests.get(cls.NAV_URL, params=params, headers=cls.HEADERS, timeout=8)
            res.raise_for_status()
            data = res.json()
            
            raw_titles = data.get("titleList", [])
            formatted = []
            
            for item in raw_titles[:limit]:
                # Extract author names safely
                authors = [a.get("name") for a in item.get("communityArtists", [])]
                author_str = ", ".join(authors) if authors else "Unknown"
                
                title_id = item.get("titleId")
                formatted.append({
                    "Rank": len(formatted) + 1,
                    "Title": item.get("titleName", "Untitled"),
                    "Author": author_str,
                    "Updated Today": "🔥 Yes" if item.get("up", False) else "No",
                    "Read Link": f"https://comic.naver.com/webtoon/list?titleId={title_id}"
                })
            return formatted
            
        except Exception as e:
            logger.error(f"Failed to fetch Naver Webtoons: {e}")
            return []


# ==========================================
# 2. STREAMLIT APP LOGIC
# ==========================================
st.set_page_config(page_title="Top 10 Today", page_icon="📈", layout="wide")

# Determine current day automatically
current_day = DirectWebtoonFetcher.get_current_day_code()

st.title(f"📈 Today's Top 10 Naver Webtoons ({current_day.upper()})")
st.write("Live, image-free rankings directly from Naver Webtoon.")

# Sidebar Controls
DAY_DISPLAY = {
    "mon": "Monday (월)", "tue": "Tuesday (화)", "wed": "Wednesday (수)",
    "thu": "Thursday (목)", "fri": "Friday (금)", "sat": "Saturday (토)", "sun": "Sunday (일)"
}

with st.sidebar:
    st.header("Settings")
    selected_day = st.selectbox(
        "Day Schedule",
        options=["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
        index=["mon", "tue", "wed", "thu", "fri", "sat", "sun"].index(current_day),
        format_func=lambda x: DAY_DISPLAY[x]
    )


# Fetch data with caching (updates every 15 mins)
@st.cache_data(ttl=900, show_spinner="Fetching live rankings...")
def load_data(day: str):
    return DirectWebtoonFetcher.fetch_top_webtoons(day=day, limit=10)


webtoons = load_data(selected_day)

# Display Results
if not webtoons:
    st.error("⚠️ Unable to load rankings at this moment. Please refresh or try again later.")
else:
    st.success(f"Loaded Top 10 for **{DAY_DISPLAY[selected_day]}**")

    # Render Clean List
    for item in webtoons:
        st.markdown(
            f"### #{item['Rank']} {item['Title']}  \n"
            f"✍️ **Author:** {item['Author']} | **Updated Today:** {item['Updated Today']}  \n"
            f"[📖 Read on Naver]({item['Read Link']})"
        )
        st.divider()

    # Compact Data Table View
    with st.expander("📊 View Clean Summary Table"):
        df = pd.DataFrame(webtoons)
        st.dataframe(
            df[["Rank", "Title", "Author", "Updated Today", "Read Link"]], 
            use_container_width=True,
            column_config={
                "Read Link": st.column_config.LinkColumn("Naver Link")
            }
        )