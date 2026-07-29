import streamlit as st
import pandas as pd
import requests

# Page Configuration
st.set_page_config(
    page_title="Top 10 Games (IGDB)",
    page_icon="🎮",
    layout="wide"
)

st.title("🎮 Weekly Top 10 Popular Games")
st.write("Fetched live via IGDB (Twitch API) based on total ratings and community activity.")

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

# 2. Helper function to query IGDB Apicalypse endpoint
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

    # Apicalypse Query: Clean string formatting without leading space issues
    query_body = (
        "fields name, total_rating, total_rating_count, cover.url, genres.name; "
        "where total_rating_count != null; "
        "sort total_rating_count desc; "
        "limit 10;"
    )

    try:
        response = requests.post(url, headers=headers, data=query_body, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data:
            st.warning("IGDB returned no records.")
            return pd.DataFrame()

        parsed_games = []
        for game in data:
            # Upgrade thumb cover URL to high-resolution cover
            cover_raw = game.get("cover", {}).get("url", "")
            cover_url = f"https:{cover_raw}".replace("t_thumb", "t_cover_big") if cover_raw else None

            # Flatten genres list into comma-separated text
            genres_list = [g['name'] for g in game.get('genres', [])] if 'genres' in game else []

            parsed_games.append({
                "Game Title": game.get("name", "Unknown"),
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
        st.subheader("🏆 IGDB Leaderboard")
        
        # Display data with image column formatting
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
