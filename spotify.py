# Connect to the Spotify API for your user
import os
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from img_utils import load_images_from_urls, pca_image_fusion, boost_saturation, encode_image
import cv2

load_dotenv()

# Establish a connection to Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=os.environ['SPOTIPY_CLIENT_ID'],
                                               client_secret=os.environ['SPOTIPY_CLIENT_SECRET'],
                                               redirect_uri=os.environ['SPOTIPY_REDIRECT_URI'],
                                               scope="ugc-image-upload playlist-modify-private playlist-modify-public"))

# Get a list of all songs in the playlist
def get_songs_from_playlist(playlist_obj):
    # From the playlist tracks URL, load all of the songs
    songlist = playlist_obj['tracks']['items']
    added = []
    for song in songlist:
        added.append({"title": song['track']['name'], "artist": song['track']['artists'][0]['name'], "plays": "", "popularity": song['track']['popularity'], "cover_url": song['track']['album']['images'][0]['url'], "spotify_ref": {"track": song['track']['id'], "album": song['track']['album']['id'], "artists": [x['id'] for x in song['track']['album']['artists']]}})
    return added

# A function that takes a playlist ID - scrapes the songs in the playlist - saves the album art - calculates an average album art and sets it as the playlist cover image
def generative_playlist_cover_art(playlistId=None):
    # Get a list of all of the playlists
    if playlistId:
        playlists = [sp.playlist(playlist_load)]
    else:
        playlists = sp.current_user_playlists()
    # For all of the playlists fetch the song lists and create a new cover art
    while playlists:
        for i, playlist in enumerate(playlists['items']):
            playlist_load = sp.playlist(playlist['uri'])
            tracks = get_songs_from_playlist(playlist_load)
            # Store all of the URLs
            image_urls = []
            for track in tracks:
                image_urls.append(track['cover_url'])
            # Load all of the images from their URLs
            images = load_images_from_urls(image_urls)
            # From the tracks create an image
            if images:
                pca_img = pca_image_fusion(images, num_components=None, decay_factor=0.9, mix=tracks, weights='popularity')
                pca_img = boost_saturation(pca_img, factor=2)
                cv2.imwrite(f"./playlist-covers/{playlist['name']}-PCA_COLLAGE.jpg", pca_img)
                b64_img = encode_image(f"./playlist-covers/{playlist['name']}-PCA_COLLAGE.jpg")
                sp.playlist_upload_cover_image(playlist['id'], b64_img)
        if playlists['next']:
            playlists = sp.next(playlists)
        else:
            playlists = None

if __name__ == "__main__":
    generative_playlist_cover_art()