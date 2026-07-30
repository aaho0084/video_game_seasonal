        response = requests.post(url, headers=headers, data=query_body, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Parse results into a clean list of dictionaries
        games_list = []
        for game in data:
            # Handle potential missing or nested fields
            cover_url = game.get("cover", {}).get("url", "")
            if cover_url and cover_url.startswith("//"):
                cover_url = "https:" + cover_url
            
            genres = [g.get("name") for g in game.get("genres", [])]
            genre_str = ", ".join(genres) if genres else "N/A"
            
            release_ts = game.get("first_release_date")
            release_date = time.strftime('%Y-%m-%d', time.gmtime(release_ts)) if release_ts else "N/A"
            
            games_list.append({
                "Title": game.get("name", "Unknown"),
                "Rating": round(game.get("total_rating", 0), 1) if game.get("total_rating") else "N/A",
                "Reviews Count": game.get("total_rating_count", 0),
                "Genres": genre_str,
                "Release Date": release_date,
                "Cover": cover_url
            })
            
        return pd.DataFrame(games_list)
    except Exception as e:
        st.error(f"Failed to fetch games from IGDB: {e}")
        return pd.DataFrame()

# 3. Main Streamlit Application UI
# Fetch keys from Streamlit secrets (highly recommended) or manual sidebar inputs
st.sidebar.header("🔑 IGDB API Configuration")
client_id = st.sidebar.text_input("Twitch Client ID", type="password", value=st.secrets.get("TWITCH_CLIENT_ID", ""))
client_secret = st.sidebar.text_input("Twitch Client Secret", type="password", value=st.secrets.get("TWITCH_CLIENT_SECRET", ""))

if client_id and client_secret:
    with st.spinner("Fetching trending games..."):
        df = fetch_igdb_top_games(client_id, client_secret)
        
    if not df.empty:
        # Display the data using Streamlit columns for layout
        for index, row in df.iterrows():
            col1, col2 = st.columns([1, 4])
            
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
        st.info("No games found or failed to load. Check your API credentials or query filters.")
else:
    st.warning("Please provide your Twitch/IGDB API credentials in the sidebar to load the leaderboard.")
