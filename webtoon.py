import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd

# Page configuration
st.set_page_config(page_title="Weekly Popularity Webtoon Rankings", layout="wide")

st.title("📱 Webtoon & Manhwa Rankings")
st.write("Browse real-time popularity and trending rankings for Webtoons powered by the AniList API.")

# Sidebar Settings
with st.sidebar:
    st.header("Search & Filter Settings")
    
    country_filter = st.selectbox(
        "Origin Country",
        options=["KR", "ALL"],
        format_func=lambda x: "South Korea (Manhwa / Webtoons)" if x == "KR" else "All Countries (Include Manga / Manhua)"
    )
    
    sort_option = st.selectbox(
        "Rank Metric",
        options=["TRENDING_DESC", "POPULARITY_DESC", "SCORE_DESC"],
        format_func=lambda x: {
            "TRENDING_DESC": "Weekly Popularity (Trending Now)",
            "POPULARITY_DESC": "Overall Popularity (Total Readers)",
            "SCORE_DESC": "Highest Score"
        }[x]
    )
    
    selected_tags = st.multiselect(
        "Webtoon Sub-Tags",
        options=["Webtoon", "Reincarnation", "Dungeon", "System", "Cultivation", "Otome Game", "Action", "Romance"],
        default=["Webtoon"]
    )
    
    item_limit = st.slider("Show Top Results", min_value=10, max_value=50, value=30, step=5)

ANILIST_URL = "https://graphql.anilist.co"

# GraphQL Query
query = """
query ($sort: [MediaSort], $tags: [String], $country: CountryCode, $perPage: Int) {
  Page(page: 1, perPage: $perPage) {
    media(type: MANGA, countryOfOrigin: $country, tag_in: $tags, sort: $sort) {
      id
      title {
        english
        romaji
      }
      averageScore
      popularity
      trending
      chapters
      volumes
      coverImage {
        large
      }
      siteUrl
      genres
      tags {
        name
      }
    }
  }
}
"""

# Construct clean variables dictionary (Omits 'country' if ALL is selected)
variables = {
    "sort": [sort_option],
    "tags": selected_tags if selected_tags else ["Webtoon"],
    "perPage": 50
}

if country_filter == "KR":
    variables["country"] = "KR"


def create_retry_session():
    """Configures automatic retries with backoff for rate limits and server errors."""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1.5,  # Wait times: 1.5s, 3s, 6s between attempts
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


@st.cache_data(ttl=3600, show_spinner="Fetching latest Webtoon rankings...")
def fetch_webtoon_data(vars_payload):
    """Fetches webtoon data with caching (1 hour) to protect against IP blocks."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    session = create_retry_session()
    
    try:
        response = session.post(
            ANILIST_URL, 
            json={'query': query, 'variables': vars_payload}, 
            headers=headers,
            timeout=12
        )
        
        if response.status_code == 200:
            return response.json().get('data', {}).get('Page', {}).get('media', [])
        elif response.status_code == 403:
            st.error("⚠️ **Cloudflare Block (403):** Streamlit Cloud's IP is currently rate-limited or blocked by AniList Cloudflare security. Try refreshing in a few minutes.")
            return []
        elif response.status_code == 429:
            st.warning("⚠️ **Rate Limit Reached (429):** Too many requests sent to AniList. Displaying cached results if available.")
            return []
        else:
            st.error(f"API Error ({response.status_code}): {response.text}")
            return []
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {e}")
        return []

# Execute Fetch
raw_webtoon_list = fetch_webtoon_data(variables)
webtoon_list = raw_webtoon_list[:item_limit]

if not webtoon_list:
    st.info("No webtoons found or data is currently unavailable. Try adjusting your sidebar filters.")
else:
    st.subheader(f"Top {len(webtoon_list)} Webtoons ({'Weekly Trending' if sort_option == 'TRENDING_DESC' else 'Ranked'})")

    # 4-Column Grid Display
    cols_per_row = 4
    cols = st.columns(cols_per_row)
    
    for index, item in enumerate(webtoon_list):
        col = cols[index % cols_per_row]
        
        title = item['title']['english'] or item['title']['romaji']
        score = f"{item['averageScore']}/100" if item['averageScore'] else "N/A"
        popularity = f"{item['popularity']:,}" if item['popularity'] else "N/A"
        trending_score = item.get('trending', 0)
        chapters = item['chapters'] if item['chapters'] else "Ongoing / Unknown"
        cover = item['coverImage']['large']
        url = item['siteUrl']
        
        with col:
            st.markdown(f"#### #{index + 1} {title}")
            st.image(cover, use_container_width=True)
            if sort_option == "TRENDING_DESC":
                st.markdown(f"📈 **Weekly Trend:** +{trending_score}")
            st.markdown(f"⭐ **Score:** {score}")
            st.markdown(f"📖 **Chapters:** {chapters}")
            st.markdown(f"👥 **Total Readers:** {popularity}")
            st.markdown(f"[Read Info on AniList]({url})")
            st.divider()

    # Data Table View
    with st.expander("📊 View Complete Data Table", expanded=False):
        df_data = []
        for rank, item in enumerate(raw_webtoon_list, start=1):
            df_data.append({
                "Rank": rank,
                "Title (English)": item['title']['english'],
                "Title (Romaji)": item['title']['romaji'],
                "Weekly Trend Score": item.get('trending', 0),
                "Average Score": item['averageScore'],
                "Total Readers": item['popularity'],
                "Chapters": item['chapters'] if item['chapters'] else "Ongoing",
                "Link": item['siteUrl']
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)