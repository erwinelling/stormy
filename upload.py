#!/usr/bin/python
# -*- coding: latin-1 -*-
import soundcloud
import os
import datetime
import sys
import shutil
from requests.exceptions import HTTPError
import logging
import ConfigParser
#
# try:
# from safeutil import move, copyfile
# except ImportError:
#     from shutil import move, copyfile

# print client.get('/me').username
# print client.access_token

# set directories to search/ move uploaded files to
# make sure these dirs for recordings & uploading exist
# make sure mopidy is owner: sudo chown mopidy:mopidy _uploaded/

# read config file
config = ConfigParser.ConfigParser()
config.read('/home/pi/stormy/stormy.cfg')

HOME_DIR = config.get("machine", "HOME_DIR")
MUSIC_DIR = config.get("machine", "MUSIC_DIR")
RECORDING_DIR_NAME = config.get("machine", "RECORDING_DIR_NAME")
RECORDING_DIR = os.path.join(MUSIC_DIR, RECORDING_DIR_NAME)
NFC_CHIP_DATA_FILE_NAME = config.get("machine", "NFC_CHIP_DATA_FILE_NAME")
NFC_CHIP_DATA_FILE = os.path.join(HOME_DIR, NFC_CHIP_DATA_FILE_NAME)

# setup logging
LOG_FILE = os.path.join(HOME_DIR, "upload.log")

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

fh = logging.FileHandler(LOG_FILE)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

# os.chdir(RECORDING_DIR)
# client = soundcloud.Client(access_token='1-35204-229958105-3a372e24e3e04a')

try:
    #create Soundcloud Client
    client = soundcloud.Client(
    # TODO: try to get this to work with just a secret key
        client_id = config.get("upload", "client_id"),
        client_secret = config.get("upload", "client_secret"),
        username = config.get("upload", "username"),
        password = config.get("upload", "password"),
    )

    # walk through all files in recording directory
    logger.debug("Checking contents of %s", RECORDING_DIR)
    from os.path import join, getsize
    count = 0
    for root, dirs, files in os.walk(RECORDING_DIR):
        for filename in files:
            # check whether it is a music file that can be uploaded to soundcloud
            # http://uploadandmanage.help.soundcloud.com/customer/portal/articles/2162441-uploading-requirements
            # AIFF, WAVE (WAV), FLAC, ALAC, OGG, MP2, MP3, AAC, AMR, and WMA
            # and ignore hidden files
            if filename.lower().endswith(('.aiff', '.wav', '.flac', '.alac', '.ogg', '.mp2', '.mp3', '.aac', '.amr', '.wma')) and not filename.startswith('.'):
                path_to_file = os.path.join(root, filename)
                not_uploaded_file = os.path.splitext(path_to_file)[0]+".notuploaded"
                if os.path.isfile(not_uploaded_file):

                    # upload to soundcloud
                    datetimenow = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M%S')
                    track = client.post('/tracks', track={
                        # TODO: Set more track data, get input somewhere
                        'title': unicode(os.path.splitext(filename)[0]),
                        'asset_data': open(path_to_file, 'rb'),
                        'description': u'Dit is een van de Jimmy\'s Verhalen. Geupload op %s.' % (datetimenow),
                        'track_type': 'spoken',
                        # 'artwork_data': open('artwork.jpg', 'rb'),
                        'purchase_url': "http://wijzijnjimmys.nl/verhalen/",
                        'license': "cc-by-nc",
                        # 'tag_list': "tag1 \"hip hop\" geo:lat=32.444 geo:lon=55.33"
                        # 'genre': 'Electronic',
                    })
                    # TODO: Add Question/ Theme to description
                    # TODO: Add more info?

                    logger.debug("Uploaded %s to Soundcloud: %s.", filename, track.permalink_url)

                    # TODO: Add Track to right Set

                    # !!!


                    # remove .notuploaded file
                    os.remove(not_uploaded_file)

                    # TODO: Make this a sync. Try to download (latest) files that are on soundcloud but not here??
                count +=1
                # logger.debug("File %s verplaatst naar: %s.",filename, new_path_to_file)
        logger.debug("Uploaded %s file(s)", count)
except HTTPError:
    logger.error("No connection to SoundCloud")
    pass
except Exception, e:
    logging.error(e, exc_info=True)
    pass

# Het is ook mogelijk om een playlist te maken, bijv. met 1 onderwerp

# # try to get a track
# try:
#     track = client.get('/tracks/1')
# except Exception, e:
#     print 'Error: %s, Status Code: %d' % (e.message, e.response.status_code)
#
# print track.title
# https://soundcloud.com# /erwinelling/patrick-watson-yellow-socks/

# Request bodies for track uploads via the API may not be larger than 500MB.

# # fetch a track by it's ID
# track = client.get('/tracks/290')
#
# # update the track's metadata
# client.put(track.uri, track={
#   'description': 'This track was recorded in Berlin',
#   'genre': 'Electronic',
#   'artwork_data': open('artwork.jpg', 'rb')
# })
logger.debug("Einde")
