import ConfigParser
import nxppy
import subprocess
import os
import time
import soundcloud
import urllib

# read config file
config = ConfigParser.ConfigParser()
config.read('stormy.cfg')

NFC_STOP_CHARACTER = config.get("machine", "NFC_STOP_CHARACTER")

mifare = nxppy.Mifare()

"""
"""

def write_nfc_string(str):
    """
    Write a string to the current NFC chip.
    """
    nr = 10
    for i in xrange(0, len(str), 4):
        uid = mifare.select()
        # print "id: %s, %s" % (nr, str[i:(i+4)])
        stukje_string = str[i:(i + 4)].ljust(4)
        mifare.write_block(nr, stukje_string)
        nr += 1
    mifare.write_block(nr, NFC_STOP_CHARACTER)


client = soundcloud.Client(client_id=config.get("upload", "client_id"))
user = client.get('/resolve', url=config.get("upload", "soundcloud_url"))
playlists = client.get('/users/%d/playlists' % user.id)
print "Available playlists on soundcloud:"
i = 0
for playlist in playlists:
    print "%s: %s" % (i, playlist.title)
    i=i+1
chosen_playlist_no = raw_input('Which playlist? ')


# args = [
#     'mpc',
#     '-h', 'localhost',
#     '-p', '6600',
#     'ls', 'SoundCloud/Sets/',
# ]
#
# p1 = subprocess.Popen(args, stdout=subprocess.PIPE)
# output, error = p1.communicate()

# print "Available playlists in virtual file system:"
# i = 0
# for line in output.split(os.linesep)[0:-1]:
#     print "%s: %s" % (i, line)
#     i=i+1
# chosen_vfs_no = raw_input('What is the corresponding local dir? ')

chosen_playlist_int = int(chosen_playlist_no)
# chosen_vfs_int= int(chosen_vfs_no)

nfc_data = {
    'id' : playlists[chosen_playlist_int].id,
    # 'title' : playlists[chosen_playlist_int].title,
    # 'vfs' : output.split(os.linesep)[chosen_vfs_int]
}

nfc_string = urllib.urlencode(nfc_data)
print "Data: %s" % (nfc_string)

previous_uid = None
while True:
    try:
        print "Hold NFC chip close to reader"
        uid = mifare.select()
        if uid and uid != previous_uid:
            print uid
            previous_uid = uid
            write_nfc_string(nfc_string)
            print "\"%s\" saved on NFC chip" % (nfc_string)
    except nxppy.SelectError:
        pass
    time.sleep(1)
