import requests, os.path, soundcloud, re, urllib, logging
import logging.handlers
import ConfigParser
import subprocess
from collections import Counter

# TODO: Also add ID3 tags based on track metadata? See e.g. https://github.com/Sliim/soundcloud-syncer/blob/master/scripts/sc-tagger

# check config
config = ConfigParser.ConfigParser()
config.read('/home/pi/stormy/stormy.cfg')
HOME_DIR = config.get("machine", "HOME_DIR")
MUSIC_DIR = config.get("machine", "MUSIC_DIR")
RECORDING_DIR_NAME = config.get("machine", "RECORDING_DIR_NAME")
RECORDING_DIR = os.path.join(MUSIC_DIR, RECORDING_DIR_NAME)

# setup logging
LOG_FILE = os.path.join(HOME_DIR, "download.log")

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

fh = logging.handlers.RotatingFileHandler(
              LOG_FILE, maxBytes=5000000, backupCount=5)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

# functions
def create_dir(dir):
    """Create directory if it does not exist"""
    if not os.path.exists(dir):
        os.makedirs(dir)

def build_file_name(dir, title):
    """Build the file name"""
    file_name = re.sub('/', '', title) + ".mp3"
    return os.path.join(dir, file_name)

def track_download_from_url(client_id, track_url, dir, override=False):
    """Download from URL"""
    client = soundcloud.Client(client_id=client_id)
    track = client.get('/resolve', url=track_url)
    return download(client, track, dir, override)

def track_download_from_id(client_id, track_id, dir, override=False):
    """Download using the song id"""
    client = soundcloud.Client(client_id=client_id)
    track = client.get('/tracks/%d' % track_id, allow_redirects=False)
    return download(client, track, dir, override)

def download(client, track, dir, override=False):
    """Download a track using the given SC client"""
    title = fix_title(track)
    logger.debug('"%s"' % title)
    if not dir: dir = 'mp3'
    create_dir(dir)
    file_name = build_file_name(dir, title)

    if not override and os.path.exists(file_name):
        logger.debug("File already exists, skipped, %s" % (file_name))
        return ""

    #TODO: if os.path exists filename with wav extensions, move to some backup folder?

    stream_url = client.get(track.stream_url, allow_redirects=False)
    urllib.urlretrieve(stream_url.location, file_name)
    return file_name

def fix_title(track):
    """Fix title (missing space, illegal chars, missing author)"""
    title = track.title
    logger.debug("Title to fix, %s" % (title))
    # user_name = track.user['username']
    #
    # # Add missing dash
    # title = re.sub(r"^(.*\S)- (.*)$", r"\1 - \2", title)
    #
    # # Remove adds
    # title = title.split('//', 1)[0]
    #
    # # Prepend username if author seems to be missing
    # if ' - ' not in title:
    #     title = '%s - %s' % (user_name, title)
    #
    # append soundcloud track ID
    title = title + ".%s" % (track.id)

    return title.strip()

def playlist_download_from_url(client_id, url, base_dir, override=False):
    """Download the given playlist"""
    downloaded = 0
    skipped = 0
    errors = 0

    # Retrieve playlist data
    client = soundcloud.Client(client_id=config.get("upload", "client_id"))
    playlist = client.get('/resolve', url=url)

    # Create dir
    # playlist_title = playlist.title
    dir = os.path.join(base_dir, "%s" % (playlist.id))
    create_dir(dir)

    # Download tracks
    for track in playlist.tracks:
        try:
            # done = song.down(client, track, dir, override)
            downloaded_file = track_download_from_id(config.get("upload", "client_id"), track['id'], dir, override)
            if downloaded_file:
                downloaded = downloaded + 1
                # "backup" files after downloading same mp3
                if os.path.exists(os.path.splitext(downloaded_file)[1]+".wav"):
                    os.rename(os.path.splitext(downloaded_file)[1]+".wav", os.path.splitext(downloaded_file)[1]+".wav.bak")
            else:
                skipped = skipped + 1
        except requests.exceptions.HTTPError, err:
            if err.response.status_code == 404:
                logger.debug('Error: could not download')
                errors = errors + 1
            else:
                raise

    logger.debug('Playlist downloaded to "%s"' % dir)
    logger.debug('Downloaded: %s, Skipped: %s, Errors: %s' % (downloaded, skipped, errors))
    return Counter({
        'downloaded': downloaded, 'skipped': skipped, 'errors': errors
    })
    # return True

def playlist_download_all(client_id, user_url, base_dir, override=False):
    """Download all playlist from the given user URL"""
    client = soundcloud.Client(client_id=client_id)
    user = client.get('/resolve', url=user_url)
    playlists = client.get('/users/%d/playlists' % user.id)

    counter = Counter()
    for playlist in playlists:
        logger.debug('Playlist: "%s"' % playlist.title)
        counter = counter + playlist_download_from_url(client_id, playlist.permalink_url, base_dir, override)
    return counter

counter = playlist_download_all(config.get("upload", "client_id"), config.get("upload", "soundcloud_url"), RECORDING_DIR)

logger.debug('Counter: "%s"' % (counter))
# playlist_download_from_url(config.get("upload", "client_id"), "https://soundcloud.com/user-787148065/sets/wat-is-jouw-favoriete-jimmys", config.get("machine", "MUSIC_DIR"))

# update local files in mopidy and restart mopidy
# TODO: import these functions and don't repeat it here
# if counter['downloaded']:
#     logger.debug('Files were downloaded. Scanning & restarting mopidy.')
#     proc = subprocess.Popen(['sudo', 'mopidyctl', 'local', 'scan'])
#     proc = subprocess.Popen(['sudo', 'systemctl', 'restart', 'mopidy'])
