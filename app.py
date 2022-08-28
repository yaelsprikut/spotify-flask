'''
    This code was based on these repositories,
    so special thanks to:
        https://github.com/datademofun/spotify-flask
        https://github.com/drshrey/spotify-flask-auth-example

'''

import json
import sys
import threading
from flask import Flask, request, redirect, g, render_template, session
from spotify_requests import spotify
from youtube_search import YoutubeSearch
app = Flask(__name__)
app.secret_key = 'some key for session'

# ----------------------- AUTH API PROCEDURE -------------------------

@app.route("/auth")
def auth():
    return redirect(spotify.AUTH_URL)


@app.route("/callback/")
def callback():
    auth_token = request.args['code']
    auth_header = spotify.authorize(auth_token)
    session['auth_header'] = auth_header
    print(auth_header)
    return profile()

def valid_token(resp):
    return resp is not None and not 'error' in resp

# -------------------------- API REQUESTS ----------------------------


@app.route("/")
def index():
    return render_template('index.html')

@app.route('/run-script')
def run_script():
    with open('data.txt', 'r', encoding='utf-8') as f:
        last_total = f.read()
    def get_track_list_len():
        threading.Timer(10.0, get_track_list_len).start()
        # # get user playlist data
        playlist_data = spotify.get_users_playlist_tracks({'Authorization': 'Bearer BQBU6WLNHUcegLrL1hcTLAX7xPAi-CmXi0gsnGliglP7k8EdGcRPftSWN9RzhpZq7NIIG_88bOsC7XurN7Fgpn-crwDtEK6QJ6WBk-E9l5Ba2eHXHbsSY98eaneY943ZGoKVYQp2relbP7uhRUYWnVueE8jUoOI4eTLhdIn36YJ3GhSRtddDv-SNJw7x5ZkQ4n0HPX81ZYEpb-FTyw8xu0x1_p0UnvPqwcn6CAqN0VYwjqM3KYBXGgBw'}, "3E9kzE2uBv5CVPX089GWyw")
        print(playlist_data)

        total_tracks = int(playlist_data["total"])
        if total_tracks == int(last_total):
            print("loop back <<<")
            return False
        print("total_tracks: ", type(total_tracks), type(last_total))
        results = YoutubeSearch("{} {}".format(playlist_data["items"][total_tracks - 1]["track"]["name"], playlist_data["items"][total_tracks - 1]["track"]["artists"][0]["name"]), max_results=10).to_dict()
        if results:
            print("results", results[0]["url_suffix"])


        with open('data.txt', 'w', encoding='utf-8') as f:
            json.dump(playlist_data["total"], f)
        # print(playlist_data)
 
    get_track_list_len()
    return "Run script for worker"

@app.route('/search/')
def search():
    if 'auth_header' in session:
        auth_header = session['auth_header']
    try:
        search_type = request.args['search_type']
        name = request.args['name']
        return make_search(search_type, name, auth_header)
    except:
        return render_template('search.html')


@app.route('/search/<search_type>/<name>')
def search_item(search_type, name):
    return make_search(search_type, name, auth_header)


def make_search(search_type, name, authHeader):
    if search_type not in ['artist', 'album', 'playlist', 'track']:
        return render_template('index.html')

    data = spotify.search(search_type, name, authHeader)
    print("data from make_search")
    print(data)
    api_url = data[search_type + 's']['href']
    items = data[search_type + 's']['items']
    return render_template('search.html',
                           name=name,
                           results=items,
                           api_url=api_url,
                           search_type=search_type)


@app.route('/artist/<id>')
def artist(id):
    if 'auth_header' in session:
        auth_header = session['auth_header']
    artist = spotify.get_artist(id, auth_header)
    print("artist response: ")
    print(artist)
    if artist['images']:
        image_url = artist['images'][0]['url']
    else:
        image_url = 'http://bit.ly/2nXRRfX'

    # tracksdata = spotify.get_artist_top_tracks(id)
    # tracks = tracksdata['tracks']

    # related = spotify.get_related_artists(id)
    # related = related['artists']

    return render_template('artist.html',
                           artist=artist,
                        #    related_artists=related,
                           image_url=image_url)




@app.route('/profile')
def profile():
    if 'auth_header' in session:
        auth_header = session['auth_header']
        # get profile data
        profile_data = spotify.get_users_profile(auth_header)

        # get user playlist data
        playlist_data = spotify.get_users_playlists(auth_header)

        # get user recently played tracks
        recently_played = spotify.get_users_recently_played(auth_header)
        
        if valid_token(recently_played):
            return render_template("profile.html",
                               user=profile_data,
                               playlists=playlist_data["items"],
                               recently_played=recently_played["items"])

    return render_template('profile.html')

@app.route('/playlist/<id>')
def playlist(id):
    if 'auth_header' in session:
        auth_header = session['auth_header']
        # get profile data
        profile_data = spotify.get_users_profile(auth_header)

        # get user playlist data
        playlist_data = spotify.get_users_playlist_tracks(auth_header, id)
         # get user recently played tracks
        recently_played = spotify.get_users_recently_played(auth_header)
        print("playlist_data")
        print(json.dumps(playlist_data, indent=4, sort_keys=True))
        if valid_token(recently_played):
            return render_template("playlist.html",
                               user=profile_data,
                               tracks=playlist_data["items"])
    return render_template('playlist.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/featured_playlists')
def featured_playlists():
    if 'auth_header' in session:
        auth_header = session['auth_header']
        hot = spotify.get_featured_playlists(auth_header)
        if valid_token(hot):
            return render_template('featured_playlists.html', hot=hot)

    return render_template('profile.html')

if __name__ == "__main__":
    app.run(debug=True, port=spotify.PORT)
