import os
import json
import boto3
import base64
import requests
from datetime import date
import csv


def handler(event, context):
    client_id = os.environ['CLIENT_ID']
    client_secret = os.environ['CLIENT_SECRET']
    # The following code to establish a token for the requests is adapted from https://stackoverflow.com/questions/65435932/spotify-api-authorization-code-flow-with-python

    # URLS
    AUTH_URL = 'https://accounts.spotify.com/authorize'
    TOKEN_URL = 'https://accounts.spotify.com/api/token'

    # Make a request to the /authorize endpoint to get an authorization code
    auth_code = requests.get(AUTH_URL, {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': 'http://savemymizes/callback',
        'scope': 'playlist-read-private',
    })

    # Encode the header 
    auth_header = base64.urlsafe_b64encode((client_id + ':' + client_secret).encode())

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic %s' % auth_header.decode('ascii')
    }

    payload = {
        'grant_type': 'client_credentials',
        'code': auth_code,
        'redirect_uri': 'http://savemymizes/callback',
        'client_id': client_id,
        'client_secret': client_secret,
    }

    # Make a request to the /token endpoint to get an access token
    access_token_request = requests.post(url=TOKEN_URL, data=payload, headers=headers)

    # Convert the response to JSON
    access_token_response_data = access_token_request.json()

    # Save the access token to a variable
    access_token = access_token_response_data['access_token']

    # Now that we have a token; track down the playlist -> first finding my user
    daily_mix_req = requests.get('https://api.spotify.com/v1/playlists/37i9dQZF1E38wUQ750W2hc', headers={'Authorization': 'Bearer ' + access_token})
    daily_mix = daily_mix_req.json()

    # Instantiate a csv to write the artists and song titles to
    filename = date.today().strftime('%Y-%m-%d') + '.csv'
    f = open('/tmp/' + filename, 'w')
    writer = csv.writer(f)

    # Iterate through the playlist to find the song name and artists
    for item in daily_mix['tracks']['items']:
        # Get the name of the song
        name = item['track']['name']
        # Get the artists
        artists = []
        for artist in item['track']['artists']:
            artists.append(artist['name'])
        # Create the line (name, artists)
        csv_line = [name, artists]
        # Write to the csv in memory
        writer.writerow(csv_line)
    f.close()

    # Reopen and read as a binary
    put_data = open('/tmp/' + filename, 'rb')

    # Upload it to an S3 bucket
    s3 = boto3.client('s3')

    try:
        s3.put_object(Body=put_data, Bucket=os.environ['BUCKET_NAME'], Key=filename)
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': os.environ['BUCKET_NAME'],
                'Key': filename
            },
            ExpiresIn=24 * 3600
        )
        return url
    except FileNotFoundError:
        print("The file was not found")
        return None


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    handler(None, None)