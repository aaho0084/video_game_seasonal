import streamlit as st
import httpx
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
### 🔑 Setup Format Reminder
Ensure your App Secrets tab exactly mimics this structure without prefixes:
```toml
TWITCH_CLIENT_ID = "your_30_char_id"
TWITCH_CLIENT_SECRET = "your_secret_key"
```
""")

# Sophisticated desktop browser signature
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# Function to get Twitch Access Token via HTTP/2
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
    
    # http2=True forces connection signatures matching real end-user browsers
    with httpx.Client(http2=True, headers=BROWSER_HEADERS, follow_redirects=True) as client:
        try:
            response = client.post(url, data=payload, timeout=12.0)
            
            if response.status_code == 200:
                return response.json().get("access_token")
                
            st.error(f"❌ Twitch Auth Server Refused Request (HTTP Status {response.status_code})")
            st.code(response.text)
        except Exception as e:
            st.error(f"❌ Transport layer failed parsing auth endpoint via HTTP/2: {e}")
    return None

# Function to fetch top trending games using PopScore popularity metrics via HTTP/2
def fetch_trending_games(client_id, access_token):
    url = "https://api.igdb.com/v4/games"
    cid = str(client_id).strip().replace('"', '').replace("'", "").replace("twitch.", "")
    
    headers = {
        **BROWSER_HEADERS,
        "Client-ID": cid,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "text/plain"
    }
    
    body = "fields name, popularity, cover.url, summary, first_release_date, total_rating; sort popularity desc; where name != null & category = 0 & popularity != null; limit 10;"
    
    with httpx.Client(http2=True, headers=headers, follow_redirects=True) as client:
        try:
            response = client.post(url, content=body, timeout=12.0)
            if response.status_code == 200:
                return response.json()
                
            st.error(f"❌ IGDB API Query Error (HTTP Status {response.status_code})")
            st.code(response.text)
        except Exception as e:
            st.error(f"❌ Transport layer failed data extraction via HTTP/2: {e}")
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
    with st.spinner("Processing token transaction via HTTP/2 tunnel..."):
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
