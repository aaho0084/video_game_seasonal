

import streamlit as st
import requests

# 1. Page Configuration
st.set_page_config(page_title="Video Game Anime Finder", layout="wide")
st.title("🎮 Seasonal Anime with Video Game Tags")

# 2. Sidebar Inputs for Season & Year
col1, col2 = st.sidebar.columns(2)
with col1:
    year = st.number_input("Year", min_value=2000, max_value=2030, value=2024)
with col2:
    season = st.selectbox("Season", ["WINTER", "SPRING", "SUMMER", "FALL"], index=2)

# 3. AniList GraphQL Configuration
ANILIST_API_URL = "https://graphql.anilist.co"

# Query filters by type (ANIME), season, year, and enforces the "Video Games" tag
GRAPHQL_QUERY = """
query ($season: MediaSeason, $seasonYear: Int) {
  Page(page: 1, perPage: 20) {
    media(season: $season, seasonYear: $seasonYear, type: ANIME, tag_in: ["Video Games"]) {
      id
      title {
        english
        romaji
      }
      coverImage {
        large
      }
      description
      episodes
      averageScore
    }
  }
}
"""

variables = {"season": season, "seasonYear": year}

# 4. Fetch Data from API
if st.sidebar.button("Fetch Anime", type="primary"):
    with st.spinner("Searching AniList..."):
        try:
            response = requests.post(
                ANILIST_API_URL, 
                json={"query": GRAPHQL_QUERY, "variables": variables}
            )
            
            if response.status_value == 200:
                anime_list = response.json()["data"]["Page"]["media"]
                
                if not anime_list:
                    st.info("No anime found with 'Video Games' tags for this season.")
                
                # 5. Display Results in a Grid layout
                for anime in anime_list:
                    with st.container(border=True):
                        c1, c2 = st.columns([1, 4])
                        with c1:
                            st.image(anime["coverImage"]["large"], use_container_width=True)
                        with c2:
                            title = anime["title"]["english"] or anime["title"]["romaji"]
                            st.subheader(title)
                            st.write(f"⭐ **Score:** {anime['averageScore'] or 'N/A'}/100 | 📺 **Episodes:** {anime['episodes'] or 'N/A'}")
                            
                            # Strip basic HTML tags from descriptions if present
                            desc = anime["description"] or "No description available."
                            st.markdown(desc, unsafe_allow_html=True)
            else:
                st.error(f"AniList API error: {response.status_value}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
