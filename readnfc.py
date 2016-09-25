import ConfigParser
import nxppy

# read config file
config = ConfigParser.ConfigParser()
config.read('stormy.cfg')

NFC_STOP_CHARACTER = config.get("machine", "NFC_STOP_CHARACTER")

mifare = nxppy.Mifare()

def read_nfc_string():
    """
    Read a string from the current NFC chip.
    """
    max_block = 1000  # if "STOP" is not found, when should we stop?
    block = 10
    output = ""
    stop = False
    count = 0
    while stop is False:
        data = mifare.read_block(block)
        if data == NFC_STOP_CHARACTER or block > max_block:
            stop = True
        else:
            output += data
        block += 1
    return output

previous_uid = None
while True:
    try:
        uid = mifare.select()
        if uid and uid != previous_uid:
            print uid
            previous_uid = uid
            nfc_string = read_nfc_string()
            print nfc_string
    except nxppy.SelectError:
        pass
    except nxppy.ReadError:
        print "ReadError"
        pass
