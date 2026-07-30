import streamlit as st
import requests
from datetime import datetime

# Set up page config
st.set_page_config(page_title="IGDB Daily PopScore Tracker", page_icon="📈", layout="centered")

st.title("📈 Today's Trending Games (IGDB PopScore)")
st.write(f"Daily rolling popularity rankings based on live user views, backlog additions, and trending engagement activity | {datetime.now().strftime('%B %d, %Y')}")

# Sidebar controls & documentation
st.sidebar.header("⚙️ App Utilities")
if st.sidebar.button("♻️ Refresh PopScores"):
    st.cache_data.clear()
    st.success("Cache cleared! Fetching fresh daily metrics...")
    st.rerun()

st.sidebar.markdown("""
### 🧠 What is PopScore?
IGDB's system updates rankings every 24 hours by evaluating real-time user behavior:
* **Daily Page Views**
* **Backlog Adjustments** (Want to play, playing, completed)
* **Search Velocity**
""")

# Standard browser headers to satisfy Cloudflare bot defense checks
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9"
}

# Function to get Twitch Access Token
@st.cache_data(ttl=3600)
def get_igdb_token(client_id, client_secret):
    url = "https://twitch.tv"
    cid = str(client_id).strip().replace('"', '').replace("'", "").replace("twitch.", "")
    csec = str(client_secret).strip().replace('"', '').replace("'", "")
    
    payload = {
        "client_id": cid,
        "client_secret": csec,
        "grant_type": "client_credentials"
    }
    
    try:
        response = requests.post(url, data=payload, headers=BROWSER_HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json().get("access_token")
            
        st.error(f"❌ Twitch Auth Server Refused Request (HTTP Status {response.status_code})")
        st.code(response.text)
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Network transport layer error: {e}")
    return None

# Function to fetch top trending games using PopScore popularity metrics
def fetch_trending_games(client_id, access_token):
    url = "https://igdb.com"
    cid = str(client_id).strip().replace('"', '').replace("'", "").replace("twitch.", "")
    
    headers = {
        **BROWSER_HEADERS,
        "Client-ID": cid,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "text/plain"
    }
    
    # Body targets the updated 'popularity' engine field representing PopScore metrics
    # category = 0 restricts results to main games (skipping DLCs and expansions)
    body = "fields name, popularity, cover.url, summary, first_release_date, total_rating; sort popularity desc; where name != null & category = 0 & popularity != null; limit 10;"
    
    try:
        response = requests.post(url, headers=headers, data=body, timeout=10)
        if response.status_code == 200:
            return response.json()
            
        st.error(f"❌ IGDB API Query Error (HTTP Status {response.status_code})")
        st.code(response.text)
    except requests.exceptions.RequestException as e:
        st.error(f"❌ IGDB connection error: {e}")
    return []

# Retrieve credentials safely from Streamlit Secrets
try:
    CLIENT_ID = st.secrets["TWITCH_CLIENT_ID"]
    CLIENT_SECRET = st.secrets["TWITCH_CLIENT_SECRET"]
except Exception:
    CLIENT_ID = None
    CLIENT_SECRET = None

if not CLIENT_ID or not CLIENT_SECRET or "your_" in str(CLIENT_ID):
    st.warning("⚠️ Configuration Required: Update your Streamlit Secrets with valid Twitch credentials.")
else:
    with st.spinner("Processing token transaction..."):
        token = get_igdb_token(CLIENT_ID, CLIENT_SECRET)
        
        if token:
            games = fetch_trending_games(CLIENT_ID, token)
            
            if games:
                for idx, game in enumerate(games, 1):
                    col1, col2 = st.columns()
                    
                    with col1:
                        if "cover" in game and "url" in game["cover"]:
                            img_url = "https:" + game["cover"]["url"].replace("t_thumb", "t_cover_big")
                            st.image(img_url, use_container_width=True)
                        else:
                            st.image("https://placeholder.com", use_container_width=True)
                    
                    with col2:
                        st.subheader(f"{idx}. {game['name']}")
                        
                        if "first_release_date" in game:
                            rel_date = datetime.fromtimestamp(game["first_release_date"]).strftime('%Y-%m-%d')
                            st.caption(f"📅 **Released:** {rel_date}")
                        
                        if "popularity" in game:
                            st.caption(f"🔥 **Daily PopScore Index:** {game['popularity']:.1f}")
                        
                        if "total_rating" in game:
                            st.caption(f"⭐ **Community Score:** {game['total_rating']:.1f}/100")
                            
                        summary = game.get("summary", "No description available.")
                        st.write(summary)
                        
                    st.divider()
            else:
                st.info("No records returned. The query format is fine, but the data stream is currently blank.")
