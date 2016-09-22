import ConfigParser
import nxppy

# read config file
config = ConfigParser.ConfigParser()
config.read('stormy.cfg')

NFC_STOP_CHARACTER = config.get("machine", "NFC_STOP_CHARACTER")

"""
TODO: Kiezen uit bestaande Soundcloud Sets ipv zelf intypen?
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

set_name = raw_input('Wat is de naam van de SoundCloud Set?')

previous_uid = None
while True:
    try:
        uid = mifare.select()
        print uid
        if uid and uid != previous_uid:
            previous_uid = uid
            write_nfc_string(set_name)
            print "%s naar de nfc chip geschreven" % (set_name)
    except nxppy.SelectError:
        pass
