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
# 1. DIRECT NAVER FETCHING LOGIC WITH FALLBACK
# ==========================================
class DirectWebtoonFetcher:
    """Fetches real-time webtoon rankings directly from Naver API with full fallback."""
    
    NAV_URL = "https://comic.naver.com/api/article/list/weekday"
    
    # Complete set of headers to bypass cloud host scraping blocks
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://comic.naver.com/webtoon",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
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
    def fetch_top_webtoons(cls, day: str, limit: int = 10) -> tuple[List[Dict[str, Any]], bool]:
        params = {"week": day.lower()}
        
        try:
            res = requests.get(cls.NAV_URL, params=params, headers=cls.HEADERS, timeout=6)
            res.raise_for_status()
            data = res.json()
            
            raw_titles = data.get("titleList", [])
            if not raw_titles:
                raise ValueError("Empty title list received")

            formatted = []
            for item in raw_titles[:limit]:
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
            return formatted, True  # True = Live data
            
        except Exception as e:
            logger.warning(f"Naver API call failed ({e}). Reverting to fallback dataset.")
            return cls.get_fallback_data(day, limit), False  # False = Fallback data

    @classmethod
    def get_fallback_data(cls, day: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Pre-cached top titles so the app NEVER fails to render."""
        fallback_database = {
            "mon": [
                {"Rank": 1, "Title": "신의 탑 (Tower of God)", "Author": "SIU", "Updated Today": "🔥 Yes", "Read Link": "https://comic.naver.com/webtoon/list?titleId=183559"},
                {"Rank": 2, "Title": "참교육 (Get Schooled)", "Author": "채용택 / 한가람", "Updated Today": "🔥 Yes", "Read Link": "https://comic.naver.com/webtoon/list?titleId=758037"},
                {"Rank": 3, "Title": "뷰티풀 군바리", "Author": "설이 / 윤성원", "Updated Today": "🔥 Yes", "Read Link": "https://comic.naver.com/webtoon/list?titleId=648419"},
                {"Rank": 4, "Title": "퀘스트지상주의", "Author": "박태준 만화회사", "Updated Today": "🔥 Yes", "Read Link": "https://comic.naver.com/webtoon/list?titleId=783052"},
                {"Rank": 5, "Title": "장씨세가 호위무사", "Author": "조형근 / 김인호", "Updated Today": "🔥 Yes", "Read Link": "https://comic.naver.com/webtoon/list?titleId=728750"}
            ],
            "wed": [
                {"Rank": 1, "Title": "전지적 독자 시점 (Omniscient Reader)", "Author": "싱숑 / 슬피쌤", "Updated Today": "🔥 Yes", "Read Link": "https://comic.naver.com/webtoon/list?titleId=747269"},
                {"Rank": 2, "Title": "화산귀환 (Return of the Blossoming Blade)", "Author": "비가 / LICO", "Updated Today": "🔥 Yes", "Read Link": "https://comic.naver.com/webtoon/list?titleId=769209"},
                {"Rank": 3, "Title": "일렉시드 (Eleceed)", "Author": "손제호 / ZHENA", "Updated Today": "🔥 Yes", "Read Link": "https://comic.naver.com/webtoon/list?titleId=717481"},
                {"Rank": 4, "Title": "먹는 인생", "Author": "홍끼", "Updated Today": "🔥 Yes", "Read Link": "https://comic.naver.com/webtoon/list?titleId=796152"},
                {"Rank": 5, "Title": "튜토리얼 탑의 고인물", "Author": "방구석김씨 / 루프", "Updated Today": "🔥 Yes", "Read Link": "https://comic.naver.com/webtoon/list?titleId=738694"}
            ]
        }
        # Return specific day fallback or default to Wednesday list
        selected_list = fallback_database.get(day.lower(), fallback_database["wed"])
        return selected_list[:limit]


# ==========================================
# 2. STREAMLIT APP LOGIC
# ==========================================
st.set_page_config(page_title="Today's Top Webtoons", page_icon="📈", layout="wide")

current_day = DirectWebtoonFetcher.get_current_day_code()

DAY_DISPLAY = {
    "mon": "Monday (월)", "tue": "Tuesday (화)", "wed": "Wednesday (수)",
    "thu": "Thursday (목)", "fri": "Friday (금)", "sat": "Saturday (토)", "sun": "Sunday (일)"
}

st.title(f"📈 Today's Top Webtoons ({DAY_DISPLAY[current_day]})")

# Sidebar Controls
with st.sidebar:
    st.header("Settings")
    selected_day = st.selectbox(
        "Day Schedule",
        options=["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
        index=["mon", "tue", "wed", "thu", "fri", "sat", "sun"].index(current_day),
        format_func=lambda x: DAY_DISPLAY[x]
    )


# Fetch data with cache
@st.cache_data(ttl=600, show_spinner="Loading webtoon rankings...")
def load_data(day: str):
    return DirectWebtoonFetcher.fetch_top_webtoons(day=day, limit=10)


webtoons, is_live = load_data(selected_day)

# Status notification
if is_live:
    st.success(f"🟢 Connected Live to Naver Webtoon ({DAY_DISPLAY[selected_day]})")
else:
    st.warning("🟡 Naver API standard stream restricted. Showing top cached titles below.")

# Display Top Webtoons
for item in webtoons:
    st.markdown(
        f"### #{item['Rank']} {item['Title']}  \n"
        f"✍️ **Author:** {item['Author']} | **Updated Today:** {item['Updated Today']}  \n"
        f"[📖 Read on Naver Webtoon]({item['Read Link']})"
    )
    st.divider()

# Summary Table
with st.expander("📊 View Data Table"):
    df = pd.DataFrame(webtoons)
    st.dataframe(
        df[["Rank", "Title", "Author", "Updated Today", "Read Link"]], 
        use_container_width=True,
        column_config={
            "Read Link": st.column_config.LinkColumn("Naver Direct Link")
        }
    )