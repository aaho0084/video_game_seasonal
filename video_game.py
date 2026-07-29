import time

@st.cache_data(ttl=86400)
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

    # Filter: Games released in the last 90 days, sorted by total ratings/hype
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
            
            # Format Unix timestamp to human-readable date
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
        df.index += 1
        return df

    except Exception as e:
        st.error(f"Error fetching data from IGDB: {e}")
        return pd.DataFrame()
