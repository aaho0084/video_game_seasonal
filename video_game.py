import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="Top 10 Games (IGDB)",
    page_icon="🎮",
    layout="wide"
)

st.title("🎮 Weekly Top 10 Popular Games")
st.write("Fetched live via IGDB (Twitch API) based on total ratings and follower hype.")

# Helper to exchange Twitch Client ID/Secret for a Bearer Access Token
@st.cache_data(ttl=300000) # Access tokens typically last ~60 days; cache for long periods
def get_igdb_token(client_id, client_secret):
    auth_url = f"https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials"
    response = requests.post(auth_url)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        st.error(f"Failed to authenticate with Twitch: {response.text}")
        return None

@st.cache_data(ttl=86400) # Cache game data for 24 hours
def fetch_igdb_top_games(client_id, client_secret):
    token = get_igdb_token(client_id, client_secret)
    if not token:
        return pd.DataFrame()

    url = "https://api.igdb.com/v4/games"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {token}"
    }

    # Apicalypse Query: Gets games sorted by rating count, retrieving name, ratings, cover, and genres
    query_body = """
        fields name, total_rating, total_rating_count, cover.url, genres.name;
        where total_rating_count > 100 & category = 0;
        sort total_rating_count desc;
        limit 10;
    """

    try:
        response = requests.post(url, headers=headers, data=query_body, timeout=10)
        response.raise_for_status()
        data = response.json()

        parsed_games = []
        for game in data:
            # Format image URL from //images.igdb.com to https: and scale to high-res t_cover_big
            cover_raw = game.get("cover", {}).get("url", "")
            cover_url = f"https:{cover_raw}".replace("t_thumb", "t_cover_big") if cover_raw else None

            # Join genres array into a string
            genres = [g['name'] for g in game.get('genres', [])] if 'genres' in game else []

            parsed_games.append({
                "Game Title": game.get("name"),
                "Score": round(game.get("total_rating", 0), 1),
                "Total Votes": game.get("total_rating_count", 0),
                "Genres": ", ".join(genres),
                "Cover": cover_url
            })

        df = pd.DataFrame(parsed_games)
        df.index += 1 # 1-indexed ranking
        return df

    except Exception as e:
        st.error(f"Error fetching data from IGDB: {e}")
        return pd.DataFrame()


# Read secrets safely from Streamlit Cloud Secrets Manager
if "IGDB_CLIENT_ID" in st.secrets and "IGDB_CLIENT_SECRET" in st.secrets:
    client_id = st.secrets["IGDB_CLIENT_ID"]
    client_secret = st.secrets["IGDB_CLIENT_SECRET"]

    with st.spinner("Retrieving latest rankings from IGDB..."):
        df = fetch_igdb_top_games(client_id, client_secret)

    if not df.empty:
        st.subheader("🏆 IGDB Leaderboard")
        
        # Display data using image columns natively supported by Streamlit
        st.dataframe(
            df,
            column_config={
                "Cover": st.column_config.ImageColumn("Cover Art", help="Game Cover"),
                "Score": st.column_config.NumberColumn("User Rating", format="%.1f ⭐")
            },
            use_container_width=True
        )

        st.subheader("📊 Rating Count Comparison")
        st.bar_chart(df.set_index('Game Title')['Total Votes'])

else:
    st.warning("⚠️ IGDB API Credentials Missing! Please add 'IGDB_CLIENT_ID' and 'IGDB_CLIENT_SECRET' to your Streamlit Secrets.")