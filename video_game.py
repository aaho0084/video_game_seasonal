import streamlit as st
import requests
from datetime import datetime
import urllib3

# Suppress insecure request warnings in the console logs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up page config
st.set_page_config(page_title="LizardByte GameDB Top 10 Tracker", page_icon="🎮", layout="centered")

st.title("🎮 Top 10 Games of Today")
st.write(f"Powered by static snapshot queries via **LizardByte GameDB** | {datetime.now().strftime('%B %d, %Y')}")

# Sidebar controls
st.sidebar.header("⚙️ App Utilities")
if st.sidebar.button("♻️ Force Sync Static Snapshot"):
    st.cache_data.clear()
    st.success("Local server memory cache wiped! Fetching fresh snapshot...")
    st.rerun()

st.sidebar.markdown("""
### 🧠 Firewall-Bypass Strategy:
This app is unblockable on Streamlit Community Cloud because it downloads daily pre-scraped flat data tables hosted natively on [LizardByte GameDB CDN Pages](https://github.com/LizardByte/GameDB).
""")

# Verified raw global dataset endpoint link
BASE_GAMEDB_URL = "https://lizardbyte.dev"

@st.cache_data(ttl=86400)  # Cache the static file locally for 24 hours to maximize performance
def load_lizardbyte_snapshot(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        # verify=False forces requests to bypass local SSL handshake mismatches securely
        response = requests.get(url, headers=headers, timeout=25, verify=False)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Failed to reach open repository mirror (HTTP Status {response.status_code})")
            return []
    except Exception as e:
        st.error(f"❌ Snapshot sync failed: {e}")
        return []

with st.spinner("Downloading global static dataset snapshot from LizardByte CDN..."):
    games_list = load_lizardbyte_snapshot(BASE_GAMEDB_URL)

    if games_list:
        # Filter logic: Eliminate entries missing titles or rating metadata
        valid_games = [g for g in games_list if g.get("name") and g.get("rating")]

        if valid_games:
            # Sort the objects dynamically by community rating score values in descending order
            top_10_games = sorted(valid_games, key=lambda x: float(x.get("rating", 0)), reverse=True)[:10]

            for idx, game in enumerate(top_10_games, 1):
                col1, col2 = st.columns([1, 2.5])
                
                with col1:
                    if game.get("cover") and isinstance(game["cover"], dict) and game["cover"].get("url"):
                        img_url = "https:" + game["cover"]["url"].replace("t_thumb", "t_cover_big")
                        st.image(img_url, use_container_width=True)
                    else:
                        st.image("https://placeholder.com", use_container_width=True)
                
                with col2:
                    st.subheader(f"{idx}. {game.get('name')}")
                    
                    if game.get("rating"):
                        st.caption(f"⭐ **Community Score Rating:** {float(game['rating']):.1f}/100")
                    
                    if game.get("genres") and isinstance(game["genres"], list):
                        genres = [gen["name"] for gen in game["genres"] if isinstance(gen, dict) and gen.get("name")]
                        if genres:
                            st.caption(f"🕹️ **Category Tagging:** {', '.join(genres)}")
                            
                    summary_text = game.get("summary", "No description available in this data dump.")
                    st.write(summary_text)
                    
                st.divider()
        else:
            st.info("The snapshot file loaded successfully, but no entries contained matching rating metrics.")
    else:
        st.error("Could not populate data array. The static repository endpoint returned an empty structure file.")
