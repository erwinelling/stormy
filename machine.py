#!/usr/bin/python
# -*- coding: latin-1 -*-
import RPi.GPIO as GPIO
import time
import datetime
import subprocess
import pygame.mixer
from pygame.mixer import Sound
import os
import signal
import nxppy
import ConfigParser
from shutil import copyfile
import logging

# read config file and set config
config = ConfigParser.ConfigParser()
config.read('/home/pi/stormy/stormy.cfg')

LED1PIN = int(config.get("machine", "LED1PIN"))
BUT1PIN = int(config.get("machine", "BUT1PIN"))
BUT2PIN = int(config.get("machine", "BUT2PIN"))
BUT3PIN = int(config.get("machine", "BUT3PIN"))
BUT4PIN = int(config.get("machine", "BUT4PIN"))
BUT5PIN = int(config.get("machine", "BUT5PIN"))
BUT6PIN = int(config.get("machine", "BUT6PIN"))
HOME_DIR = config.get("machine", "HOME_DIR")
MUSIC_DIR = config.get("machine", "MUSIC_DIR")
NFC_READER_PRESENT = bool(config.get("machine", "NFC_READER_PRESENT"))
NFC_STOP_CHARACTER = config.get("machine", "NFC_STOP_CHARACTER")
SOUND_CARD = config.get("machine", "SOUND_CARD")
SOUND_CARD_NO = config.get("machine", "SOUND_CARD_NO")
SOUND_CARD_MIC_NAME = config.get("machine", "SOUND_CARD_MIC_NAME")
SOUNDCLOUD_DEFAULT_SET = config.get("machine", "SOUNDCLOUD_DEFAULT_SET")
SOUNDCLOUD_SET_PATH = config.get("machine", "SOUNDCLOUD_SET_PATH")

RECORDING_DIR_NAME = config.get("machine", "RECORDING_DIR_NAME")
RECORDING_DIR = os.path.join(MUSIC_DIR, RECORDING_DIR_NAME)
RECORDING_PROCESS_ID_FILE_NAME = config.get("machine", "RECORDING_PROCESS_ID_FILE_NAME")
RECORDING_PROCESS_ID_FILE = os.path.join(HOME_DIR, RECORDING_PROCESS_ID_FILE_NAME)
NFC_CHIP_DATA_FILE_NAME = config.get("machine", "NFC_CHIP_DATA_FILE_NAME")
NFC_CHIP_DATA_FILE = os.path.join(HOME_DIR, NFC_CHIP_DATA_FILE_NAME)

# setup logging
LOG_FILE = os.path.join(HOME_DIR, "machine.log")

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

try:
    # Pin Setup:
    GPIO.setmode(GPIO.BOARD)  # Broadcom pin-numbering scheme

    # Initiate LEDs:
    if LED1PIN:
        GPIO.setup(LED1PIN, GPIO.OUT)
        GPIO.output(LED1PIN, GPIO.LOW)

    # Initiate buttons:
    if BUT1PIN:
        # Button pin set as input w/ pull-up
        GPIO.setup(BUT1PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(BUT1PIN, GPIO.FALLING, bouncetime=200)
    if BUT2PIN:
        # Button pin set as input w/ pull-up
        GPIO.setup(BUT2PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(BUT2PIN, GPIO.FALLING, bouncetime=200)
    if BUT3PIN:
        # Button pin set as input w/ pull-up
        GPIO.setup(BUT3PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(BUT3PIN, GPIO.FALLING, bouncetime=200)
    if BUT4PIN:
        # Button pin set as input w/ pull-up
        GPIO.setup(BUT4PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(BUT4PIN, GPIO.FALLING, bouncetime=200)
    if BUT5PIN:
        # Button pin set as input w/ pull-up
        GPIO.setup(BUT5PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(BUT5PIN, GPIO.FALLING, bouncetime=200)
    if BUT6PIN:
        # Button pin set as input w/ pull-up
        GPIO.setup(BUT6PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(BUT6PIN, GPIO.FALLING, bouncetime=200)

    # Initiate NFC reader:
    mifare = nxppy.Mifare()

    def check_file_path_exists(filepath):
        if not os.path.exists(os.path.dirname(filepath)):
            try:
                original_umask = os.umask(0)
                os.makedirs(os.path.dirname(filepath), 0777)
            except:
                raise
            finally:
                os.umask(original_umask)


    def save_upload_datafile(filepath):
        check_file_path_exists(filepath)
        f = open(filepath, 'w')
        f.close()

    def save_soundcloud_set_datafile(filepath):
        """
        Copy data file content to sound specific data file.
        If no data file was there, write file for Soundcloud Test set.
        """
        if os.path.isfile(NFC_CHIP_DATA_FILE):
            check_file_path_exists(filepath)
            copyfile(NFC_CHIP_DATA_FILE, filepath)
        else:
            check_file_path_exists(NFC_CHIP_DATA_FILE)
            f = open(filepath, 'w')
            f.write(SOUNDCLOUD_DEFAULT_SET)
            f.close()


    def get_soundcloud_set():
        """
        """
        try:
            f = open(NFC_CHIP_DATA_FILE)
            current_soundcloud_set = f.readline().strip()
            f.close()
        except:
            current_soundcloud_set = SOUNDCLOUD_DEFAULT_SET
            pass

        logger.debug("SoundCloud Set is %s", current_soundcloud_set)
        return current_soundcloud_set

    def get_soundcloud_set_name(soundcloud_set_path=""):
        if not soundcloud_set_path:
            current_soundcloud_set_name = get_soundcloud_set().replace(SOUNDCLOUD_SET_PATH, "")
        else:
            current_soundcloud_set_name = soundcloud_set_path.replace(SOUNDCLOUD_SET_PATH, "")
        logger.debug("SoundCloud Set Name is %s", current_soundcloud_set_name)
        return current_soundcloud_set_name

    def check_playing():
        """
        Helper function to see whether some song is playing.
        MPC returns filename etc on mpc status when a file is being played.
        If not, it returns some general info, starting with volume.
        We check this info and return true when playing and false if not.
        """
        status = subprocess.check_output(['mpc', 'status']).decode("utf-8")

        if status[:6] == "volume" or "[paused]" in status:
            # this is the output when the song is stopped
            logger.debug("Playing? No")
            return False
        else:
            logger.debug("Playing? Yes")
            return True

    def check_paused():
        status = subprocess.check_output(['mpc', 'status']).decode("utf-8")

        if "[paused]" in status:
            logger.debug("Paused? Yes")
            return True
        else:
            logger.debug("Paused? No")
            return False

    def take_picture(filepath):
        """
        Take a picture with the first available webcam device.
        """
        # proc = subprocess.Popen(['fswebcam', '-d', '/dev/video1', '-r' , '1280x720', '--no-banner', name])
        logger.debug("Taking picture: %s", filepath)
        proc = subprocess.Popen(['fswebcam', '-r', '1280x720', '--no-banner', filepath])

    def record_sound(filepath):
        """
        Do some audio recording
        e.g. arecord -D plughw:CARD=Device,DEV=0 -f S16_LE -c1 -r44100 -V mono test.wav
        """
        logger.debug("Recording %s started.", filepath)
        # Turn on Mic
        args = [
            'amixer',
            '-c', SOUND_CARD_NO,
            'set',
            SOUND_CARD_MIC_NAME,
            'cap',
            '13'
        ]
        subprocess.Popen(args)

        args = [
            'arecord',
            '-D', SOUND_CARD,
            '-f', 'S16_LE',
            '-c1',
            '-r44100',
            '-V', 'mono',
            '--process-id-file', RECORDING_PROCESS_ID_FILE,
            filepath
        ]
        proc = subprocess.Popen(args)

    def check_recording():
        """
        Helper function to see whether something is being recorded.
        """
        if os.path.isfile(RECORDING_PROCESS_ID_FILE):
            logger.debug("Recording? Yes")
            return True
        else:
            logger.debug("Recording? No")
            return False

    def stop_recording():
        """
        Kill the recording process.
        """
        pidfile = os.path.join(HOME_DIR, RECORDING_PROCESS_ID_FILE)
        f = open(pidfile)
        pid = int(f.readline().strip())
        f.close()
        logger.debug("Stopping recording process by killing PID %s", str(pid))
        os.kill(pid, signal.SIGINT)

    def control_mpc(action):
        """
        Run mpc commands to control Mopidy Music server.
        """
        logger.debug("MPC %s", action)
        proc = subprocess.Popen(['mpc', '-h', 'localhost', '-p', '6600', action, '-q'])

    def mpc_update_local_files():
        proc = subprocess.Popen(['sudo', 'mopidyctl', 'local', 'scan'])

    def load_playlist(playlist=SOUNDCLOUD_DEFAULT_SET):
        """
        Change playlist in Mopidy

        # mpc clear
        # mpc ls SoundCloud/Sets/
        """
        local_playlist = os.path.join(RECORDING_DIR, get_soundcloud_set_name(playlist))
        logger.debug("loading SoundCloud playlist %s (Local version:)", playlist, local_playlist)

        control_mpc('stop')
        control_mpc('clear')

        # TODO rewrite control_mpc to make it work with more than 1 argument (*args? or append to list)
        args = [
            'mpc',
            '-h', 'localhost',
            '-p', '6600',
            'ls', playlist,
        ]
        p1 = subprocess.Popen(args, stdout=subprocess.PIPE)
        output, error = p1.communicate()
        # TODO: Check for errors here, i.e. "error: Not found" when SoundCloud not loaded
        # lines = subprocess.check_output(args, shell=True)
        for line in output.split(os.linesep):
            # quotedline = '"%s"' % line
            # print quotedline
            # TODO rewrite control_mpc to make it work with more than 1 argument
            song = subprocess.Popen(['mpc', 'add', line])

        # write playlist info to file
        logger.debug("writing '%s' to %s", playlist, NFC_CHIP_DATA_FILE)

        check_file_path_exists(NFC_CHIP_DATA_FILE)
        f = open(NFC_CHIP_DATA_FILE, 'w')
        f.write(playlist)
        f.close()

        logger.debug("changed playlist")

        # for debugging purposes, start playing it when there are no buttons
        if not BUT1PIN:
            control_mpc('play')

    def blink(number, sleep=0.5):
        """
        Blink led 1
        """
        if LED1PIN:
            for i in range(0,number):
                GPIO.output(LED1PIN, GPIO.HIGH)
                time.sleep(sleep)
                GPIO.output(LED1PIN, GPIO.LOW)
                time.sleep(sleep)
                logger.debug("Blink")

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
        return output.rstrip()

    def nfc_callback(uid):
        """
        Function that decides what to do when an NFC chips is presented, based on the uid of the chip.

        """
        nfc_data = read_nfc_string()
        logger.debug("Read \"%s\"", nfc_data)
        blink(2)

        if nfc_data == "EIND":
            button_stop()
            return True
        if nfc_data == "PLAY":
            button_play()
            return True
        if nfc_data == "REC":
            button_rec()
            return True
        if nfc_data[0:16] == SOUNDCLOUD_SET_PATH:
            load_playlist(nfc_data)
        else:
            load_playlist()

        return True

    def button_feedback():
        """
        Give feedback on button press.
        """
        # buttonSound.play()
        # proc = subprocess.Popen(['aplay', os.path.join(HOME_DIR, "button.wav")])
        logger.debug("Button feedback")
        blink(1)

    def button_rec():
        """
        """
        logger.debug("REC button")

        if not check_recording():
            if check_playing():
                control_mpc('stop')
            if LED1PIN:
                GPIO.output(LED1PIN, GPIO.HIGH)

            # Set the filenames
            current_datetime = "%s" % (datetime.datetime.now())
            soundcloud_set_file_name = "%s.setname" % (current_datetime)
            picture_file_name = "%s.jpg" % (current_datetime)
            sound_file_name = "%s.wav" % (current_datetime)
            upload_file_name = "%s.notuploaded" % (current_datetime)

            # Set the file paths
            soundcloud_set_name = get_soundcloud_set_name()
            logger.debug("%s", RECORDING_DIR)
            soundcloud_set_file = os.path.join(RECORDING_DIR, soundcloud_set_name, soundcloud_set_file_name)
            picture_file = os.path.join(RECORDING_DIR, soundcloud_set_name, picture_file_name)
            sound_file = os.path.join(RECORDING_DIR, soundcloud_set_name, sound_file_name)
            upload_file = os.path.join(RECORDING_DIR, soundcloud_set_name, upload_file_name)

            # Save the files
            logger.debug("%s", soundcloud_set_file)
            save_soundcloud_set_datafile(soundcloud_set_file)

            logger.debug("%s", picture_file)
            take_picture(picture_file)

            logger.debug("%s", sound_file)
            record_sound(sound_file)

            logger.debug("%s", upload_file)
            save_upload_datafile(upload_file)
        else:
            pass

    def button_prev():
        """
        """
        logger.debug("PREV button")
        if check_playing():
            button_feedback()
            control_mpc('prev')

        else:
            pass

    def button_play():
        """
        """
        logger.debug("PLAY button")
        if not check_playing():
            button_feedback()
            control_mpc('play')
        else:
            pass

    def button_next():
        """
        """
        logger.debug("NEXT button")
        if check_playing():
            button_feedback()
            control_mpc('next')
        else:
            pass

    def button_stop():
        """
        """
        logger.debug("STOP button")
        if check_recording():
            stop_recording()
            mpc_update_local_files()
            if LED1PIN:
                GPIO.output(LED1PIN, GPIO.LOW)

        if check_playing():
            button_feedback()
            control_mpc('stop')
        else:
            pass

    def button_pause():
        """
        """
        logger.debug("PAUSE button")
        if check_playing():
            button_feedback()
            if check_paused():
                control_mpc("play")
            else:
                control_mpc('pause')
        else:
            pass

    # Startup
    # Restart Mopidy because somehow Soundcloud is mostly not working when the service has started on bot
    logger.debug("Starting. Press CTRL+C to exit")
    logger.debug("Waiting 30 seconds to restart Mopidy.")
    # time.sleep(30)
    logger.debug("Restarting Mopidy and waiting 3 seconds.")
    proc = subprocess.Popen(['sudo', 'systemctl', 'restart', 'mopidy'])
    time.sleep(3)
    mpc_update_local_files()
    logger.debug("OK, here we go!")
    blink(3)

    # Load initial playlist
    load_playlist()

    # Check for input from buttons and NFC reader
    previous_uid = None
    while True:
        if NFC_READER_PRESENT == True:
            try:
                uid = mifare.select()
                if uid and uid != previous_uid:
                    logger.debug("NFC detected (%s)", uid)
                    previous_uid = uid
                    nfc_callback(uid)
            except nxppy.SelectError:
                # No card found
                pass
            except nxppy.ReadError:
                logger.error("NXP ReadError (%s): Probably no valid data on chip", uid)
                pass

        if BUT1PIN and GPIO.event_detected(BUT1PIN):
                button_rec()
        if BUT2PIN and GPIO.event_detected(BUT2PIN):
                button_prev()
        if BUT3PIN and GPIO.event_detected(BUT3PIN):
                button_next()
        if BUT4PIN and GPIO.event_detected(BUT4PIN):
                button_stop()
        if BUT5PIN and GPIO.event_detected(BUT5PIN):
                button_play()
        if BUT6PIN and GPIO.event_detected(BUT6PIN):
                button_pause()

        # wait a second before checking again
        time.sleep(1)

except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly:
    GPIO.cleanup()  # cleanup all GPIO
except Exception, e:
    logging.error(e, exc_info=True)
