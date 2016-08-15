#!/usr/bin/python
# -*- coding: latin-1 -*-
import soundcloud
import os
import datetime
import sys
import shutil
from requests.exceptions import HTTPError
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
# TODO: create dirs on the fly?
MUSIC_DIR = "/home/pi/Music/"
RECORDING_DIR = os.path.join(MUSIC_DIR, "Local/")
UPLOADING_DIR = os.path.join(MUSIC_DIR, "Soundcloud/")

# os.chdir(RECORDING_DIR)
# client = soundcloud.Client(access_token='1-35204-229958105-3a372e24e3e04a')

try:
    #create Soundcloud Client
    client = soundcloud.Client(
    # TODO: maybe get this from mopipidy settings
    # TODO: try to get this to work with just a secret key
        client_id='2afa000b9c16670dd62c83700567487f',
        client_secret='dbf7e4b8b8140f142b62c8e93b4d0ab8',
        username='erwin@uptous.nl',
        password='ell82SOU',
    )

    # walk through all files in recording directory
    print "Checking contents of %s" % RECORDING_DIR
    from os.path import join, getsize
    count = 0
    for root, dirs, files in os.walk(RECORDING_DIR):
        print files
        for filename in files:
            # check whether it is a music file that can be uploaded to soundcloud
            # http://uploadandmanage.help.soundcloud.com/customer/portal/articles/2162441-uploading-requirements
            # AIFF, WAVE (WAV), FLAC, ALAC, OGG, MP2, MP3, AAC, AMR, and WMA
            # and ignore hidden files
            if filename.lower().endswith(('.aiff', '.wav', '.flac', '.alac', '.ogg', '.mp2', '.mp3', '.aac', '.amr', '.wma')) and not filename.startswith('.'):
                path_to_file = os.path.join(root, filename)

                # upload to soundcloud
                datetimenow = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M%S')
                track = client.post('/tracks', track={
                    # TODO: Set more track data, get input somewhere
                    'title': unicode(os.path.splitext(filename)[0]),
                    'asset_data': open(path_to_file, 'rb'),
                    'description': u'Opgenomen met Jimmy Story Sucker. Geupload op %s.' % (datetimenow),
                    'track_type': 'spoken',
                    # 'artwork_data': open('artwork.jpg', 'rb'),
                    'purchase_url': "http://biechtstoel.uptous.nl",
                    'license': "cc-by-nc",
                    # 'tag_list': "tag1 \"hip hop\" geo:lat=32.444 geo:lon=55.33"
                    # 'genre': 'Electronic',
                })
                print "File %s geupload naar Soundcloud: %s." % (filename, track.permalink_url)

                # move file to uploaded directory
                if not os.path.exists(UPLOADING_DIR):
                    os.makedirs(UPLOADING_DIR)
                new_filename = "%s-%s%s" % (os.path.splitext(filename)[0],datetimenow,os.path.splitext(filename)[1])
                new_path_to_file = os.path.join(UPLOADING_DIR, new_filename)
                shutil.move(path_to_file, new_path_to_file)
                count +=1
                print "File %s verplaatst naar: %s." % (filename, new_path_to_file)
        print "%s file(s) geupload." % (count)
except HTTPError:
    # TODO: Better error handling
    # TODO: Some logging?
    print("Geen verbinding met Soundcloud mogelijk")
    pass

print("Einde")
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
