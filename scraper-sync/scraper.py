# Instead of using the Spotify WEB Api to get the Daily Mixes use some lovely playwright Scraping
from playwright.sync_api import sync_playwright
import os
from datetime import datetime
import time
import json

# Instead of just retrieving and printing the playlists to the terminal I want to create a folder for the date and a JSON file for each of the playlists
if os.getenv("DOCKERIZED"):
    HISTORY_PATH = "/app/output"
else:
    HISTORY_PATH = "./daily-mix"
# Get today's date and create a 'new' folder name to then check if it exists
today = datetime.today()
formatted_date = today.strftime("%Y-%m-%d")
newpath = HISTORY_PATH + '/' + formatted_date
if not os.path.exists(newpath):
    os.makedirs(newpath)

# REPLACE THESE WITH YOUR OWN PLAYLIST IDs USING THE WEB CLIENT
playlist_ids = {
    'Daily Mix 1': '37i9dQZF1E38wUQ750W2hc',
    'Daily Mix 2': '37i9dQZF1E37989BIHbI44',
    'Daily Mix 3': '37i9dQZF1E39DxOGG335PJ',
    'Daily Mix 4': '37i9dQZF1E37LiZdlVfP5X',
    'Daily Mix 5': '37i9dQZF1E36PoGX3COHX1',
    'Daily Mix 6': '37i9dQZF1E35FlVvIKsn2j',
    "Riley Daily Mix 1": "37i9dQZF1E38pkkdXfiMgT",
    "Riley Daily Mix 2": "37i9dQZF1E37gAKPin9ftd",
    "Riley Daily Mix 3": "37i9dQZF1E38ZrbxANczm8"
}

# Use playwright to scrape the playlists from the Web Client as Spotify removed API access - thanks Spotify
def scrape_spotify_playlist_api_via_playwright(url, api_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Because Spotify lazy loads the playlist pages we want to increase the limit for the request that retrieves the songs - from 25 to 50 (the size of the Daily Mix playlist)
        def handle(route, request):
            # Check if the request URL matches
            if api_url in request.url:
                # Increase the limit from 25 to 50 to capture the entire playlist
                modified_url = request.url.replace('3A25', '3A50')
                # Continue the request with the new URL leaving everything else the same
                route.continue_(url=modified_url)
            else:
                route.continue_()

        # Attach this method to the page listening to all routes
        page.route("**/*", handle)

        # Create a shared variable to store tracks gathered from the responses
        tracks = []

        # Define a callback function to intercept and capture the API request
        def handle_response(response):
            # Check if the response matches the API URL you are interested in
            if api_url in response.url:
                # Extract the JSON data from the response
                playlist_data = response.json()
                print(playlist_data)
                # Extract relevant track information
                items = playlist_data['data']['playlistV2']['content']['items']

                for item in items:
                    # Basic Data
                    title = item['itemV2']['data']['name']
                    artist = ', '.join(artist['profile']['name'] for artist in item['itemV2']['data']['albumOfTrack']['artists']['items'])
                    plays = item['itemV2']['data']['playcount']
                    cover = item['itemV2']['data']['albumOfTrack']['coverArt']['sources'][0]['url']
                    # Spotify Ref Ids
                    artist_ids = [artist['uri'].replace('spotify:artist:', '') for artist in item['itemV2']['data']['albumOfTrack']['artists']['items']]
                    track_id = item['itemV2']['data']['uri'].replace('spotify:track:', '')
                    album_id = item['itemV2']['data']['albumOfTrack']['uri'].replace('spotify:album:', '')
                    tracks.append({'title': title, 'artist': artist, 'plays': plays, 'cover_url': cover, 'spotify_ref': {'track': track_id, 'album': album_id, 'artists': artist_ids}})
            return response

        # Attach the callback to intercept responses
        page.on('response', handle_response)

        # Navigate to the page (no need to scrape it, just open it to make the network request)
        page.goto(url, timeout=60000)

        # Once the response is processed, close the browser and return the tracks
        browser.close()

        return tracks

# The URL for the playlist page (you can use any Spotify playlist page URL)
api_url = "https://api-partner.spotify.com/pathfinder/v1/query?operationName=fetchPlaylist&"

for playlist_name, playlist_url in playlist_ids.items():
    time.sleep(30)
    # Fetch the tracks by capturing the API response via Playwright
    tracks = scrape_spotify_playlist_api_via_playwright(f"https://open.spotify.com/playlist/{playlist_url}", api_url)

    # Based on the tracks scraped - create a JSON file for the playlist
    if tracks:
        with open(f"{newpath}/{playlist_name.replace(' ', '-')}.json", "w") as final:
            print(f'JSON BEING CREATED FOR {playlist_name} IN {newpath}')
            json.dump(tracks, final)

    # # Print all extracted songs
    # for idx, track in enumerate(tracks, start=1):
    #     print(f"{idx}. {track['title']} - {track['artist']}")

    # print(f"{playlist_name} Total songs fetched: {len(tracks)} 🎶")
    # break