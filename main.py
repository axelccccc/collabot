import spotipy, twitter
import json, os, random, re, sys, argparse
from spotipy.oauth2 import SpotifyClientCredentials



########## SETTINGS ##########



SPOTIFY_API_KEY             = ""
SPOTIFY_API_SECRET          = ""
TWITTER_CONSUMER_KEY        = ""
TWITTER_CONSUMER_SECRET     = ""
TWITTER_ACCESS_TOKEN        = ""
TWITTER_ACCESS_TOKEN_SECRET = ""
TWITTER_BEARER_TOKEN        = ""

ARTISTS_DATA_PATH = "./artists.json"



########## API CLIENTS ##########



# Spotify API client

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_API_KEY, 
    client_secret=SPOTIFY_API_SECRET,
    requests_timeout=60,))

# Twitter client

twit = twitter.Api(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)



########## COMMAND-LINE ##########



parser = argparse.ArgumentParser(
    description="Collabot",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("-g", "--get", help="takes program in artist retrieval mode")
parser.add_argument("-p", "--playlist", help="retrieve artists from playlist")
parser.add_argument("-r", "--recursive", action="store_true", help="retrieve recursively from playlist's artists' related section")
parser.add_argument("-d", "--depth", type=int, help="depth of artist retrieval recursiveness")
parser.add_argument("-n", "--number", type=int, help="number of related artists retrieved")
parser.add_argument("-f", "--file", type=str, help="file in which to store retrieved artists")

parser.add_argument("-a", "--artists", type=str, help="if in generation mode (default), specific file to use to generate collabs (default: artists.json)")

parser.add_argument("-i", "--interactive", action="store_true", help="Shows result and asks for confirmation before tweeting")



########## DATA ##########



def load_json_data(filepath):
    path = os.path.dirname(os.path.abspath(filepath))

    try:
        if not os.path.isdir(path):
            os.makedirs(path)
        with open(filepath) as f:
            if os.path.getsize(filepath):
                data = json.load(f)
                return data
            else:
                return []
    except FileNotFoundError:
        with open(filepath, 'w') as f:
            return []

def save_json_data(data, filepath, mode):
    path = os.path.dirname(os.path.abspath(filepath))

    if not os.path.isdir(path):
        os.makedirs(path)

    with open(filepath, mode) as f:
        json.dump(data, f, indent=4)



########## SPOTIFY API ##########



def get_artists_playlist(playlist_id, artists: list = None):
    """Get artists from a Spotify playlist
        :param: playlist_id : Spotify playlist ID
        :artists: if provided, append new artists to the list of existing ones
    """
    counter = 0
    if artists == None:
        artists = []
    seed_playlist = sp.playlist(playlist_id, fields="tracks.items(track(artists(name, id)))")
    for track in seed_playlist['tracks']['items']:
        for artist in track['track']['artists']:
            a = {
                    'name': artist['name'],
                    'id': artist['id']
            }
            if not artists.count(a):
                artists.append(a)
                counter += 1
    print(f'{counter} artists added from playlist')
    return artists



def get_related_artists(artists: list, depth=1, num_per_artist=5, counter=0):
    """ Get related artists recursively.
        :param: artists : [{name, id}, {name, id}...]
        :param: depth : level of recursion
        :param: num_per_artist : number of related artists returned (max 20)
        :param: counter : ignore — don't assign
    """
    if num_per_artist > 20:
        num_per_artist = 20
    if not depth:
        return []
    else:
        related_artists = []
        for i in range(0, len(artists)):
            recommandations = sp.artist_related_artists(artists[i]['id'])
            for artist in recommandations['artists'][:num_per_artist]:
                a = {
                    'name': artist['name'],
                    'id': artist['id']
                }
                if (
                    not related_artists.count(a) and 
                    not artists.count(a)
                ):
                    related_artists.append(a)
                    counter += 1
        related_artists.extend(get_related_artists(
            related_artists, depth=depth-1, num_per_artist=num_per_artist, counter=counter))
        print(f'{counter} related artists added')
        return related_artists



def get_artists_from_seed_playlist(playlist_id, depth=1, num_per_artist=5,artists=None):
    """Gets artists from a playlist, and a number of related artists per artist, recursively"""
    artists = get_artists_playlist(playlist_id, artists)
    artists.extend(get_related_artists(artists, depth, num_per_artist))
    return artists



def get_album_tracks(album):
    """Returns all the tracks from an album"""
    tracks = []
    results = sp.album_tracks(album['id'])
    tracks.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks

def get_discography(artist):
    """Returns all the tracks from all the albums of artist"""
    albums = []
    tracks = []
    results = sp.artist_albums(artist['id'], album_type='album')
    albums.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        albums.extend(results['items'])
    unique = set()  # skip duplicate albums
    for album in albums:
        name = album['name'].lower()
        if name not in unique:
            unique.add(name)
            tracks.extend(get_album_tracks(album))
    return tracks
        
def get_discography_songtitles(artist):
    """Returns all song titles from an artist's discography (albums only)"""
    titles = []
    tracks = get_discography(artist)
    for track in tracks:
        titles.append(track['name'])
    return titles



########## COLLAB ##########



def generate_random_collab(artists: list):
    """Selects some artists from the database randomly and returns the list of them"""
    collab = []
    num_artists = random.choices([1, 2, 3, 4, 5], [0.90, 0.075, 0.02, 0.00375, 0.00125], k=1)
    for i in range(0, num_artists[0]+1):
        x = random.randint(0, len(artists))
        while collab.count(artists[x]):
            x = random.randint(0, len(artists))
        collab.append(artists[x])
            
    return collab



########## FORMATTING ##########



def remove_feat(title: str):
    """If existing, removes the part listing the featurings from a song title"""
    title = title.strip(u'\u200e')
    # pattern = re.compile(r'(?i).*(?=\(f(?:ea)?t)')
    splitted = re.split(r'(?i)[ ([]?f(?:ea)?t(?:\.)?', title)
    return splitted[0]

def format_titles(titles):
    """ Removes feats, titles pertaining to live versions, remixes, remasters...
        :param: titles : list of song titles by artist :
                    {
                        'artist': ['song1', 'song2', ...],
                        'artist2': ['song1', 'song2', ...]
                    }
    """
    keywords = ['Live', 'Remastered', 'Version', 'Remix', 'Bonus', 'Instrumental', 'Mix']
    for artist, songs in titles.items():
        for i in range(0, len(songs)):
            songs[i] = remove_feat(songs[i])
        for k in keywords:
            pattern = '.*'+k+'.*'
            r = re.compile(pattern,flags=re.I)
            songs = [s for s in songs if s not in list(filter(r.match,songs))]
            # songs = list(filter(r.match,songs))
        titles[artist] = songs
    return titles



def format_prompt_msg(collab):
    """ Format the message that is sent to OpenAI for completion
        :param: collab : artists of the collab
        :param: titles : discography of all those artists
    """
    titles = {}
    for artist in collab:
        titles[artist['name']] = get_discography_songtitles(artist)
    titles = format_titles(titles)
    msg = []
    for artist, songs in titles.items():
        msg.append('Artist: ' + artist + '\nSong titles: ' + ', '.join(songs))
    #msg = '\n'.join(msg)
    msg = ''
    msg += ('\nA collaboration between ' + ', '.join(list(titles.keys())[:-1]) + ' and ' + list(titles.keys())[-1] 
            + ' would be called')
    return msg



########## TEMP ##########



def generate_collab_song_temp(collab):
    """ Temporary version : only formats artists names (while finding a solution for generating titles)
    """
    txt = f"{collab[0]['name']} (ft. {' & '.join([a['name'] for a in collab[1:]])})"
    return txt



########## TWITTER ##########



def tweet(message):
    try:
        status = twit.PostUpdate(message)
        print(f'Posted "{status.text}" on {status.user.name}')
    except UnicodeDecodeError:
        print("Your message could not be encoded.  Perhaps it contains non-ASCII characters? ")
        print("Try explicitly specifying the encoding with the --encoding flag")
        sys.exit(2)



########## MAIN ##########



def main():

    artists = []

    args = parser.parse_args()

    if args.get: # artist retrieval mode

        get_playlist = args.playlist or ""
        get_depth = args.depth or 1
        get_number = args.number or 5

        if get_playlist != "":

            if args.recursive:
                artists = get_artists_from_seed_playlist(
                    get_playlist, 
                    depth=get_depth, 
                    num_per_artist=get_number)
            else:
                artists = get_artists_playlist(get_playlist, artists)

            if args.file: 
                save_json_data(artists, args.file, 'w')

        else:
            print("Specify a spotify playlist ID to retrieve artists")


    else: # collab generation mode

        if args.artists:
            artists = load_json_data(args.artists)
        else:
            artists = load_json_data(ARTISTS_DATA_PATH)

        collab = generate_random_collab(artists)
        collab_txt = generate_collab_song_temp(collab)

        if args.interactive:
            print(collab_txt)
            tweet_confirm = input("Tweet result ? (Y/n) ")[0].lower()
            if tweet_confirm == "y":
                tweet(collab_txt)
            
        else:
            tweet(collab_txt)
    


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(err)