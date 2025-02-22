import os
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

def get_songs_from_playlist(playlist_obj):
    songlist = playlist_obj['tracks']['items']
    added = []
    for song in songlist:
        added.append(song['track']['uri'])
    return added

# Establish a connection to Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=os.environ['SPOTIPY_CLIENT_ID'],
                                               client_secret=os.environ['SPOTIPY_CLIENT_SECRET'],
                                               redirect_uri=os.environ['SPOTIPY_REDIRECT_URI'],
                                               scope=""
))

# Get a list of all of the playlists
playlists = sp.current_user_playlists()
# playlists = sp.playlist('37i9dQZF1E38wUQ750W2hc')
while playlists:
    for i, playlist in enumerate(playlists['items']):
        print("%4d %s %s" % (i + 1 + playlists['offset'], playlist['uri'],  playlist['name']))
    if playlists['next']:
        playlists = sp.next(playlists)
    else:
        playlists = None