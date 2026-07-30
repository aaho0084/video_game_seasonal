import streamlit as st
import requests
from datetime import datetime

# Set up page config
st.set_page_config(page_title="Top 10 Games Today", page_icon="🎮", layout="centered")

st.title("🎮 Top 10 Games of Today")
st.write(f"Based on global engagement metrics from **IGDB** | {datetime.now().strftime('%B %d, %Y')}")

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
Get credentials from the [Twitch Developer Portal](https://dev.twitch.tv/). Add them to your Streamlit App Secrets:
```toml
TWITCH_CLIENT_ID = "your_actual_client_id"
TWITCH_CLIENT_SECRET = "your_actual_client_secret"
```
""")

# Function to get Twitch Access Token
@st.cache_data(ttl=3600)  # Cache token for 1 hour
def get_igdb_token(client_id, client_secret):
    url = "https://twitch.tv"
    
    # Strip quotes only, leaving the string raw for validation
    cid = str(client_id).strip().replace('"', '').replace("'", "")
    csec = str(client_secret).strip().replace('"', '').replace("'", "")
    
    payload = {
        "client_id": cid,
        "client_secret": csec,
        "grant_type": "client_credentials"
    }
    
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            st.error(f"❌ Twitch Auth Server Refused Access (Status {response.status_code})")
            st.code(response.text)
    except Exception as e:
        st.error(f"❌ Server Connection Failed during authentication step: {e}")
    return None

# Function to fetch top popular games using resilient parameters
def fetch_top_games(client_id, access_token):
    url = "https://igdb.com"
    headers = {
        "Client-ID": client_id.strip().replace('"', '').replace("'", ""),
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "text/plain"
    }
    
    # Explicit query structure for maximum engine stability across datasets
    body = "fields name, rating_count, cover.url, summary, first_release_date, total_rating; sort rating_count desc; where name != null & category = 0 & rating_count != null; limit 10;"
    
    try:
        response = requests.post(url, headers=headers, data=body)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ IGDB API Query Error {response.status_code}")
            st.code(response.text)
            return []
    except Exception as e:
        st.error(f"❌ API Connection Failed: {e}")
        return []

# Retrieve credentials safely from Streamlit Secrets
try:
    CLIENT_ID = st.secrets["TWITCH_CLIENT_ID"]
    CLIENT_SECRET = st.secrets["TWITCH_CLIENT_SECRET"]
except Exception:
    CLIENT_ID = None
    CLIENT_SECRET = None

if not CLIENT_ID or not CLIENT_SECRET or "your_" in str(CLIENT_ID):
    st.warning("⚠️ Configuration Required: Please update your Streamlit Secrets with valid credentials from the Twitch Developer Portal.")
else:
    with st.spinner("Fetching today's top games..."):
        token = get_igdb_token(CLIENT_ID, CLIENT_SECRET)
        if token:
            games = fetch_top_games(CLIENT_ID, token)
            
            if games:
                for idx, game in enumerate(games, 1):
                    col1, col2 = st.columns([1, 3])
                    
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
                            st.caption(f"📈 **Active Players Voted:** {game['rating_count']}")
                            
                        summary = game.get("summary", "No description available.")
                        st.write(summary)
                        
                    st.divider()
            else:
                st.info("The dashboard connected successfully, but the IGDB query layer returned zero results.")
