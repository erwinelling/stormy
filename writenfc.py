import ConfigParser
import nxppy
import subprocess
import os

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
        mifare.write_block(nr, str[i:(i + 4)])
        nr += 1
    mifare.write_block(nr, NFC_STOP_CHARACTER)

args = [
    'mpc',
    '-h', 'localhost',
    '-p', '6600',
    'ls', 'SoundCloud/Sets/',
]

p1 = subprocess.Popen(args, stdout=subprocess.PIPE)
output, error = p1.communicate()

print "Available SoundCloud/Sets:"
i = 0
for line in output.split(os.linesep)[0:-1]:
    print "%s: %s" % (i, line)
    i=i+1
    print "x: Something else"

chosen_set = raw_input('Which set number (or x)?')

if chosen_set == "x":
    set_name = chosen_set
else:
    chosen_set_int = int(chosen_set)
    set_name = output.split(os.linesep)[chosen_set_int]

previous_uid = None
while True:
    try:
        uid = mifare.select()
        print uid
        if uid and uid != previous_uid:
            previous_uid = uid
            write_nfc_string(set_name)
            print "%s saved on NFC chip" % (set_name)
    except nxppy.SelectError:
        pass
