import streamlit as st
import requests
from datetime import datetime

# Set up page config
st.set_page_config(page_title="Top 10 Games Today", page_icon="🎮", layout="centered")

st.title("🎮 Top 10 Games of Today")
st.write(f"Based on live popularity metrics from **IGDB** | {datetime.now().strftime('%B %d, %Y')}")

# Sidebar instructions for deployment setup
st.sidebar.header("⚙️ Deployment Setup")
st.sidebar.markdown("""
### GitHub & Streamlit Cloud Setup:
1. Save this code as `app.py`.
2. Create a `requirements.txt` file containing:
   ```text
   streamlit
   requests
   ```
3. Push both files to a **GitHub repository**.
4. Log into [Streamlit Community Cloud](https://streamlit.io).
5. Click **New app**, select your repo, and deploy!

### 🔑 IGDB API Credentials
Get your credentials from the [Twitch Developer Portal](https://dev.twitch.tv/). Add them to your Streamlit App Secrets (`.streamlit/secrets.toml` locally or in the Cloud settings):
```toml
TWITCH_CLIENT_ID = "your_client_id"
TWITCH_CLIENT_SECRET = "your_client_secret"
```
""")

# Function to get Twitch Access Token
@st.cache_data(ttl=3600)  # Cache token for 1 hour
def get_igdb_token(client_id, client_secret):
    url = "https://twitch.tv"
    
    # Passing credentials safely via params prevents URL host-parsing issues
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    
    try:
        response = requests.post(url, params=payload)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            st.error(f"Auth Error {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"Authentication Request Failed: {e}")
    return None

# Function to fetch top popular games
def fetch_top_games(client_id, access_token):
    url = "https://igdb.com"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "text/plain"
    }
    
    # Fixed query layout string
    body = "fields name, popularity, cover.url, summary, first_release_date, total_rating; sort popularity desc; where name != null & category = 0; limit 10;"
    
    try:
        response = requests.post(url, headers=headers, data=body)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"IGDB API Error {response.status_code}: {response.text}")
            return []
    except Exception as e:
        st.error(f"API Connection Failed: {e}")
        return []

# Retrieve credentials from Streamlit Secrets
try:
    CLIENT_ID = st.secrets["TWITCH_CLIENT_ID"]
    CLIENT_SECRET = st.secrets["TWITCH_CLIENT_SECRET"]
except Exception:
    CLIENT_ID = None
    CLIENT_SECRET = None

if not CLIENT_ID or not CLIENT_SECRET:
    st.warning("⚠️ Missing IGDB API Credentials! Please configure `TWITCH_CLIENT_ID` and `TWITCH_CLIENT_SECRET` in your Streamlit Secrets.")
else:
    with st.spinner("Fetching today's top games..."):
        token = get_igdb_token(CLIENT_ID, CLIENT_SECRET)
        if token:
            games = fetch_top_games(CLIENT_ID, token)
            
            if games:
                for idx, game in enumerate(games, 1):
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        # Handle cover image
                        if "cover" in game and "url" in game["cover"]:
                            img_url = "https:" + game["cover"]["url"].replace("t_thumb", "t_cover_big")
                            st.image(img_url, use_container_width=True)
                        else:
                            st.image("https://placeholder.com", use_container_width=True)
                    
                    with col2:
                        st.subheader(f"{idx}. {game['name']}")
                        
                        # Format Release Date
                        if "first_release_date" in game:
                            rel_date = datetime.fromtimestamp(game["first_release_date"]).strftime('%Y-%m-%d')
                            st.caption(f"📅 **Released:** {rel_date}")
                        
                        # Format Rating
                        if "total_rating" in game:
                            st.caption(f"⭐ **Rating:** {game['total_rating']:.1f}/100")
                            
                        # Summary description
                        summary = game.get("summary", "No description available.")
                        st.write(summary)
                        
                    st.divider()
