import streamlit as st
import pandas as pd
import requests
import time  # <--- Fixes the NameError!

# Page Configuration
st.set_page_config(
    page_title="Top 10 Recent Games (IGDB)",
    page_icon="🎮",
    layout="wide"
)

st.title("🎮 Top 10 Popular Recent Games")
st.write("Fetched live via IGDB (Twitch API) showing trending titles released in the last 90 days.")

# 1. Helper function to authenticate with Twitch OAuth2
@st.cache_data(ttl=300000)  # Cache access token for long periods (~3.4 days)
def get_igdb_token(client_id, client_secret):
    auth_url = (
        f"https://id.twitch.tv/oauth2/token"
        f"?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials"
    )
    headers = {"User-Agent": "StreamlitGameRanker/1.0"}
    
    try:
        response = requests.post(auth_url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        st.error(f"Failed to authenticate with Twitch: {e}")
        return None

# 2. Helper function to query IGDB for games released in the last 90 days
@st.cache_data(ttl=86400)  # Cache game data for 24 hours to preserve API limits
def fetch_igdb_top_games(client_id, client_secret):
    token = get_igdb_token(client_id, client_secret)
    if not token:
        return pd.DataFrame()

    url = "https://api.igdb.com/v4/games"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {token}",
        "User-Agent": "StreamlitGameRanker/1.0"
    }

    # Calculate Unix timestamp for 90 days ago
    ninety_days_ago = int(time.time()) - (90 * 86400)

    # Filter: Games released in the last 90 days, sorted by total rating activity
    query_body = (
        f"fields name, total_rating, total_rating_count, cover.url, genres.name, first_release_date; "
        f"where first_release_date > {ninety_days_ago} & total_rating_count != null; "
        f"sort total_rating_count desc; "
        f"limit 10;"
    )

    try:
        response = requests.post(url, headers=headers, data=query_body, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data:
            st.warning("No recent games found for this timeframe.")
            return pd.DataFrame()

        parsed_games = []
        for game in data:
            cover_raw = game.get("cover", {}).get("url", "")
            cover_url = f"https:{cover_raw}".replace("t_thumb", "t_cover_big") if cover_raw else None
            genres_list = [g['name'] for g in game.get('genres', [])] if 'genres' in game else []
            
            # Format Unix timestamp to human-readable date string
            release_ts = game.get("first_release_date")
            release_date = pd.to_datetime(release_ts, unit='s').strftime('%Y-%m-%d') if release_ts else "N/A"

            parsed_games.append({
                "Game Title": game.get("name", "Unknown"),
                "Release Date": release_date,
                "Score": round(game.get("total_rating", 0), 1),
                "Total Votes": game.get("total_rating_count", 0),
                "Genres": ", ".join(genres_list),
                "Cover": cover_url
            })

        df = pd.DataFrame(parsed_games)
        df.index += 1  # 1-indexed ranking
        return df

    except Exception as e:
        st.error(f"Error fetching data from IGDB: {e}")
        return pd.DataFrame()


# 3. Main Application Logic & Secret Handling
if "IGDB_CLIENT_ID" in st.secrets and "IGDB_CLIENT_SECRET" in st.secrets:
    client_id = st.secrets["IGDB_CLIENT_ID"]
    client_secret = st.secrets["IGDB_CLIENT_SECRET"]

    with st.spinner("Retrieving latest rankings from IGDB..."):
        df = fetch_igdb_top_games(client_id, client_secret)

    if not df.empty:
        st.subheader("🏆 IGDB Leaderboard (Recent Releases)")
        
        # Display data with image and formatted number columns
        st.dataframe(
            df,
            column_config={
                "Cover": st.column_config.ImageColumn("Cover Art", help="Game Cover"),
                "Score": st.column_config.NumberColumn("User Rating", format="%.1f ⭐")
            },
            use_container_width=True
        )

        st.subheader("📊 Popularity Breakdown (Total Votes)")
        st.bar_chart(df.set_index('Game Title')['Total Votes'])

else:
    st.warning("⚠️ IGDB Credentials missing! Add `IGDB_CLIENT_ID` and `IGDB_CLIENT_SECRET` in your Streamlit Cloud Secrets Manager.")
