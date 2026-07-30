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
st.write("Fetched live via IGDB (Twitch API) showing trending titles released in the last 30 days.")

# 1. Helper function to authenticate with Twitch OAuth2 - Safe to cache strings
@st.cache_data(ttl=300000)
def get_igdb_token(client_id, client_secret):
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

# 2. Main data fetching function - Removed cache_data decorator to stop TypeError serialization failures
def fetch_igdb_top_games(client_id, client_secret):
    token = get_igdb_token(client_id, client_secret)
    if not token:
        return pd.DataFrame()

    url = "https://api.igdb.com/v4/games"
    headers = {
        "Client-ID": client_id.strip(),
        "Authorization": f"Bearer {token}",
        "User-Agent": "StreamlitGameRanker/1.0"
    }

    # Calculate Unix timestamp for 30 days ago
    thirty_days_ago = int(time.time()) - (30 * 86400)

    # RESTRUCTURED QUERY: Grabs trending releases sorted by date, with fallback sorting mechanisms
    query_body = (
        f"fields name, total_rating, total_rating_count, cover.url, genres.name, first_release_date, hypes; "
        f"where first_release_date > {thirty_days_ago}; "
        f"sort first_release_date desc; "
        f"limit 40;"
    )

    try:
        response = requests.post(url, headers=headers, data=query_body, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Double check that we actually have an array payload
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
            
            # Cast elements strictly to stop TypeErrors during DataFrame creation
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
        
        # In-memory sorting: Sort by Hype Score first, then fallback to Review Counts
        df = df.sort_values(by=["Hype Score", "Reviews Count"], ascending=False).head(10).reset_index(drop=True)
        return df
        
    except Exception as e:
        st.error(f"Failed to fetch games from IGDB: {e}")
        return pd.DataFrame()

# 3. Main Streamlit Application UI
tmol_secrets = st.secrets.get("tmol", {})
client_id = tmol_secrets.get("TWITCH_CLIENT_ID", "")
client_secret = tmol_secrets.get("TWITCH_CLIENT_SECRET", "")

if client_id and client_secret:
    with st.spinner("Loading recent releases..."):
        df = fetch_igdb_top_games(client_id, client_secret)
        
    if df is not None and not df.empty:
        for index, row in df.iterrows():
            col1, col2 = st.columns([1, 4])
            
            with col1:
                if row["Cover"] and "placeholder" not in row["Cover"]:
                    st.image(row["Cover"], use_container_width=True)
                else:
                    st.image("https://placeholder.com", use_container_width=True)
                    
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
        st.info("The API connected successfully, but no matching games were found within this 30-day window.")
else:
    st.error("⚠️ Secrets not found! Please verify your Streamlit App settings dashboard configuration structure.")
