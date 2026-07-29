import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Current Season Video Game Anime", layout="wide")

st.title("🎮 Current Season Video Game Anime")
st.write("Live ranking of current season anime tagged with **Video Games** using the AniList API.")

# Sidebar Filters
with st.sidebar:
    st.header("Filter Options")
    season = st.selectbox("Season", ["SUMMER", "FALL", "WINTER", "SPRING"], index=0)
    year = st.number_input("Year", min_value=2000, max_value=2030, value=2026)
    
    sort_option = st.selectbox(
        "Rank By",
        options=["SCORE_DESC", "POPULARITY_DESC", "TRENDING_DESC"],
        format_func=lambda x: {
            "SCORE_DESC": "Highest Average Score",
            "POPULARITY_DESC": "Most Popular",
            "TRENDING_DESC": "Trending Now"
        }[x]
    )

# GraphQL Query
ANILIST_URL = "https://graphql.anilist.co"

query = """
query ($season: MediaSeason, $seasonYear: Int, $sort: [MediaSort], $tags: [String]) {
  Page(page: 1, perPage: 50) {
    media(season: $season, seasonYear: $seasonYear, tag_in: $tags, type: ANIME, sort: $sort) {
      id
      title {
        english
        romaji
      }
      averageScore
      popularity
      episodes
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

variables = {
    "season": season,
    "seasonYear": year,
    "sort": [sort_option],
    "tags": ["Video Games", "Virtual World", "E-Sports"]
}

@st.cache_data(ttl=3600)  # Caches results for 1 hour
def fetch_anime_data(variables):
    # Full browser User-Agent to ensure Cloudflare doesn't block server-side requests
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.post(
            ANILIST_URL, 
            json={'query': query, 'variables': variables}, 
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json().get('data', {}).get('Page', {}).get('media', [])
        else:
            st.error(f"API Error ({response.status_code}): {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {e}")
        return []

anime_list = fetch_anime_data(variables)

if not anime_list:
    st.info("No video game anime found for this season/year selection.")
else:
    st.subheader(f"Ranked List ({len(anime_list)} Found)")

    # Grid Display
    cols = st.columns(3)
    for index, item in enumerate(anime_list):
        col = cols[index % 3]
        
        title = item['title']['english'] or item['title']['romaji']
        score = item['averageScore'] if item['averageScore'] else "N/A"
        cover = item['coverImage']['large']
        url = item['siteUrl']
        
        with col:
            st.markdown(f"### #{index + 1} {title}")
            st.image(cover, use_container_width=True)
            st.markdown(f"⭐ **Score:** {score}/100 | 🔥 **Popularity:** {item['popularity']}")
            st.markdown(f"📺 **Episodes:** {item['episodes'] if item['episodes'] else 'TBD'}")
            st.markdown(f"[View on AniList]({url})")
            st.divider()

    # Data Table View
    st.subheader("Data Overview")
    df_data = []
    for rank, item in enumerate(anime_list, start=1):
        df_data.append({
            "Rank": rank,
            "Title": item['title']['english'] or item['title']['romaji'],
            "Score": item['averageScore'],
            "Popularity": item['popularity'],
            "Genres": ", ".join(item['genres']),
            "Link": item['siteUrl']
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True)