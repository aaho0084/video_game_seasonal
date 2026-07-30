import streamlit as st
import requests
from datetime import datetime

# Set up page config
st.set_page_config(page_title="Top 10 Games Today", page_icon="🎮", layout="centered")

st.title("🎮 Top 10 Games of Today")
st.write(f"Based on engagement metrics from **IGDB** | {datetime.now().strftime('%B %d, %Y')}")

# Sidebar controls & documentation
st.sidebar.header("⚙️ App Utilities")
if st.sidebar.button("♻️ Clear Cache & Force Re-auth"):
    st.cache_data.clear()
    st.success("Cache wiped! Reloading credentials...")
    st.rerun()

st.sidebar.markdown("""
### 🔑 Setup Format Reminder
Ensure your App Secrets tab exactly mimics this structure without prefixes:
```toml
TWITCH_CLIENT_ID = "your_30_char_id"
TWITCH_CLIENT_SECRET = "your_secret_key"
```
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
        # Pass browser headers along with form data payload
        response = requests.post(url, data=payload, headers=BROWSER_HEADERS, timeout=10)
        
        if response.status_code == 200:
            return response.json().get("access_token")
            
        st.error(f"❌ Twitch Auth Server Refused Request (HTTP Status {response.status_code})")
        st.code(response.text)
        
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Network transport layer error: {e}")
    return None

# Function to fetch top popular games using resilient parameters
def fetch_top_games(client_id, access_token):
    url = "https://igdb.com"
    
    cid = str(client_id).strip().replace('"', '').replace("'", "").replace("twitch.", "")
    
    # Merge browser signatures with API validation headers
    headers = {
        **BROWSER_HEADERS,
        "Client-ID": cid,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "text/plain"
    }
    
    # Standard fallback indexing array query
    body = "fields name, rating_count, cover.url, summary, first_release_date, total_rating; sort rating_count desc; where name != null & category = 0 & rating_count != null; limit 10;"
    
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
            games = fetch_top_games(CLIENT_ID, token)
            
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
                        
                        if "total_rating" in game:
                            st.caption(f"⭐ **Rating:** {game['total_rating']:.1f}/100")
                        elif "rating_count" in game:
                            st.caption(f"📈 **Review Count:** {game['rating_count']}")
                            
                        summary = game.get("summary", "No description available.")
                        st.write(summary)
                        
                    st.divider()
            else:
                st.info("No records matched the current indexing rules filter.")
