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
st.write("Fetched live via IGDB (Twitch API) showing trending titles released in the last 7 days.")

# 1. Helper function to authenticate with Twitch OAuth2
@st.cache_data(ttl=300000)
def get_igdb_token(client_id, client_secret):
    # Construct exact target endpoint URL
    auth_url = "https://id.twitch.tv/oauth2/token"
    
    # Passing arguments via explicit dictionary data payload ensures standard URL form encoding
    payload = {
        "client_id": client_id.strip(),
        "client_secret": client_secret.strip(),
        "grant_type": "client_credentials"
    }
    headers = {"User-Agent": "StreamlitGameRanker/1.0"}
    
    try:
        response = requests.post(auth_url, data=payload, headers=headers, timeout=10)
        
        # Catch explicit status failures before processing JSON
        if response.status_code != 200:
            st.error(f"⚠️ Twitch Auth Failed! Status Code: {response.status_code}")
            st.code(response.text) # Prints text error string directly on your app canvas
            return None
            
        return response.json().get("access_token")
    except Exception as e:
        st.error(f"Failed to authenticate with Twitch: {e}")
        return None

# 2. Helper function to query IGDB for games released in the last 7 days
@st.cache_data(ttl=14400)
def fetch_igdb_top_games(client_id, client_secret):
    token = get_igdb_token(client_id, client_secret)
    if not token:
        return pd.DataFrame()

    url = "https://igdb.com"
    headers = {
        "Client-ID": client_id.strip(),
        "Authorization": f"Bearer {token}",
        "User-Agent": "StreamlitGameRanker/1.0"
    }

    # Calculate Unix timestamp for 7 days ago
    seven_days_ago = int(time.time()) - (7 * 86400)

    # Filter: Recent titles matching window
    query_body = (
        f"fields name, total_rating, total_rating_count, cover.url, genres.name, first_release_date; "
        f"where first_release_date > {seven_days_ago}; "
        f"sort first_release_date desc; "
        f"limit 10;"
    )

    try:
        response = requests.post(url, headers=headers, data=query_body, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        games_list = []
        for game in data:
            cover_url = game.get("cover", {}).get("url", "")
            if cover_url and cover_url.startswith("//"):
                cover_url = "https:" + cover_url
            
            if "t_thumb" in cover_url:
                cover_url = cover_url.replace("t_thumb", "t_cover_big")
            
            genres = [g.get("name") for g in game.get("genres", [])]
            genre_str = ", ".join(genres) if genres else "N/A"
            
            release_ts = game.get("first_release_date")
            release_date = time.strftime('%Y-%m-%d', time.gmtime(release_ts)) if release_ts else "N/A"
            
            games_list.append({
                "Title": game.get("name", "Unknown"),
                "Rating": round(game.get("total_rating", 0), 1) if game.get("total_rating") else "N/A",
                "Reviews Count": game.get("total_rating_count", 0) if game.get("total_rating_count") else 0,
                "Genres": genre_str,
                "Release Date": release_date,
                "Cover": cover_url
            })
            
        return pd.DataFrame(games_list)
    except Exception as e:
        st.error(f"Failed to fetch games from IGDB: {e}")
        return pd.DataFrame()

# 3. Main Streamlit Application UI
tmol_secrets = st.secrets.get("tmol", {})
client_id = tmol_secrets.get("p3p6uzalq7goirss68gg50v5iy30mv", "")
client_secret = tmol_secrets.get("4dzxgc818qa0faepyrd4k2ffrhixg1", "")

# Fallback setup - replace placeholder strings inside the quotes below
if not client_id or not client_secret:
    client_id = "p3p6uzalq7goirss68gg50v5iy30mv"       
    client_secret = "4dzxgc818qa0faepyrd4k2ffrhixg1" 

# Verify keys aren't default unedited template strings
if client_id and "YOUR_REAL" not in client_id:
    with st.spinner("Fetching trending games..."):
        df = fetch_igdb_top_games(client_id, client_secret)
        
    if not df.empty:
        for index, row in df.iterrows():
            col1, col2 = st.columns()
            
            with col1:
                if row["Cover"]:
                    st.image(row["Cover"], use_container_width=True)
                else:
                    st.image("https://placeholder.com", use_container_width=True)
                    
            with col2:
                st.subheader(f"{index + 1}. {row['Title']}")
                st.write(f"📅 **Release Date:** {row['Release Date']}")
                st.write(f"🏷️ **Genres:** {row['Genres']}")
                st.write(f"⭐ **Rating:** {row['Rating']} / 100 ({row['Reviews Count']} votes)")
            st.divider()
    else:
        st.info("The API connected successfully, but returned 0 games for this 7-day window.")
else:
    st.error("⚠️ Credentials missing! Replace placeholder strings inside the script file.")
