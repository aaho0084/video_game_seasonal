import streamlit as st
import pandas as pd
import requests
import time

# Page Configuration
st.set_page_config(
    page_title="Top 10 Recent Games (IGDB)",
    page_icon="🎮",
    layout="wide"
)

st.title("🎮 Top 10 Popular Recent Games")
st.write("Fetched live via IGDB (Twitch API) showing trending titles released in the last 90 days.")

# 1. Helper function to authenticate with Twitch OAuth2 - Cached safely as a string
@st.cache_data(ttl=3600)  # Twitch tokens expire in ~60 days, caching for 1 hour is safe and efficient
def get_igdb_token(client_id, client_secret):
    # FIX: Corrected Twitch OAuth2 endpoint URL
    auth_url = "https://twitch.tv"
    payload = {
        "client_id": client_id.strip(),
        "client_secret": client_secret.strip(),
        "grant_type": "client_credentials"
    }
    headers = {"User-Agent": "StreamlitGameRanker/1.0"}
    
    try:
        response = requests.post(auth_url, data=payload, headers=headers, timeout=10)
        if response.status_code != 200:
            st.error(f"⚠️ Twitch Auth Failed! Status Code: {response.status_code}")
            st.code(response.text)
            return None
        return response.json().get("access_token")
    except Exception as e:
        st.error(f"Failed to authenticate with Twitch: {e}")
        return None

# 2. Main data fetching function
def fetch_igdb_top_games(client_id, client_secret):
    token = get_igdb_token(client_id, client_secret)
    if not token:
        return pd.DataFrame()

    # FIX: Corrected IGDB v4 API endpoint URL for games
    url = "https://igdb.com"
    headers = {
        "Client-ID": client_id.strip(),
        "Authorization": f"Bearer {token}",
        "User-Agent": "StreamlitGameRanker/1.0"
    }

    # Window of 90 days (90 days * 24 hours * 3600 seconds)
    ninety_days_ago = int(time.time()) - (90 * 86400)

    # Queries recent releases over the last 90 days, returning up to 50 for local sorting
    query_body = (
        f"fields name, total_rating, total_rating_count, cover.url, genres.name, first_release_date, hypes; "
        f"where first_release_date > {ninety_days_ago}; "
        f"sort first_release_date desc; "
        f"limit 50;"
    )

    try:
        response = requests.post(url, headers=headers, data=query_body, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data or not isinstance(data, list):
            return pd.DataFrame()
            
        games_list = []
        for game in data:
            if not isinstance(game, dict):
                continue
                
            cover_url = game.get("cover", {}).get("url", "") if game.get("cover") else ""
            if cover_url and cover_url.startswith("//"):
                cover_url = "https:" + cover_url
            
            if "t_thumb" in cover_url:
                cover_url = cover_url.replace("t_thumb", "t_cover_big")
            
            genres = [g.get("name") for g in game.get("genres", []) if isinstance(g, dict)]
            genre_str = ", ".join(genres) if genres else "N/A"
            
            release_ts = game.get("first_release_date")
            release_date = time.strftime('%Y-%m-%d', time.gmtime(release_ts)) if release_ts else "N/A"
            
            games_list.append({
                "Title": str(game.get("name", "Unknown")),
                "Rating": float(game.get("total_rating")) if game.get("total_rating") else None,
                "Reviews Count": int(game.get("total_rating_count")) if game.get("total_rating_count") else 0,
                "Hype Score": int(game.get("hypes")) if game.get("hypes") else 0,
                "Genres": genre_str,
                "Release Date": release_date,
                "Cover": str(cover_url)
            })
            
        if not games_list:
            return pd.DataFrame()
            
        df = pd.DataFrame(games_list)
        
        # Sort locally using multiple criteria (Hype, review volume) to capture true popularity balance
        df = df.sort_values(by=["Hype Score", "Reviews Count"], ascending=False).head(10).reset_index(drop=True)
        return df
        
    except Exception as e:
        st.error(f"Failed to fetch games from IGDB: {e}")
        return pd.DataFrame()

# 3. Main Streamlit Application UI
# FIX: Adjusted parsing syntax to pull directly from the root level of Streamlit secrets
client_id = st.secrets.get("TWITCH_CLIENT_ID", "")
client_secret = st.secrets.get("TWITCH_CLIENT_SECRET", "")

if client_id and client_secret:
    with st.spinner("Loading recent releases..."):
        df = fetch_igdb_top_games(client_id, client_secret)
        
    if df is not None and not df.empty:
        for index, row in df.iterrows():
            col1, col2 = st.columns([1, 4]) # FIX: Balanced column layouts for cleaner UI
            
            with col1:
                # FIX: Used a reliable fallback placeholder image URL
                if row["Cover"] and "placeholder" not in row["Cover"]:
                    st.image(row["Cover"], use_container_width=True)
                else:
                    st.image("https://placehold.co", use_container_width=True)
                    
            with col2:
                st.subheader(f"{index + 1}. {row['Title']}")
                st.write(f"📅 **Release Date:** {row['Release Date']}")
                st.write(f"🏷️ **Genres:** {row['Genres']}")
                if row["Hype Score"] > 0:
                    st.write(f"🔥 **Hype Score:** {row['Hype Score']}")
                
                rating_val = row["Rating"]
                if pd.notna(rating_val) and rating_val is not None:
                    st.write(f"⭐ **Rating:** {round(rating_val, 1)} / 100 ({row['Reviews Count']} votes)")
                else:
                    st.write("⭐ **Rating:** N/A (Not enough reviews yet)")
            st.divider()
    else:
        st.info("The API connected successfully, but no matching games were found within this 90-day window.")
else:
    st.error("⚠️ Secrets not found! Please verify your Streamlit App settings dashboard configuration structure.")
