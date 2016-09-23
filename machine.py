#!/usr/bin/python
# -*- coding: latin-1 -*-
import RPi.GPIO as GPIO
import time
import datetime
import subprocess
from subprocess import Popen
import pygame.mixer
from pygame.mixer import Sound
import os
import signal
import nxppy
import ConfigParser
from shutil import copyfile
import logging

# read config file
config = ConfigParser.ConfigParser()
config.read('/home/pi/stormy/stormy.cfg')

GROUNDPIN = int(config.get("machine", "GROUNDPIN"))
LED1PIN = int(config.get("machine", "LED1PIN"))
LED2PIN = int(config.get("machine", "LED2PIN"))
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

RECORDING_DIR_NAME = config.get("machine", "RECORDING_DIR_NAME")
RECORDING_DIR = os.path.join(MUSIC_DIR, RECORDING_DIR_NAME)
RECORDING_PROCESS_ID_FILE_NAME = config.get("machine", "RECORDING_PROCESS_ID_FILE_NAME")
RECORDING_PROCESS_ID_FILE = os.path.join(HOME_DIR, RECORDING_PROCESS_ID_FILE_NAME)
NFC_CHIP_DATA_FILE_NAME = config.get("machine", "NFC_CHIP_DATA_FILE_NAME")
NFC_CHIP_DATA_FILE = os.path.join(HOME_DIR, NFC_CHIP_DATA_FILE_NAME)

LOG_FILE = os.path.join(HOME_DIR, "machine.log")

# setup logging
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

"""
# Debugging
TODO: Make sure soundcloud is loaded on reboot
TODO: Add buttons and test
TODO: Finish implementing pause button (check behaviour of pause funtion)
TODO: check if i can stop the static noise
TODO: Test recording
TODO: Find out why MPD server gives timeouts sometimes when using MPC (different with python?)
TODO: Maybe switch to https://github.com/Mic92/python-mpd2
TODO: make sure the script works without internet connection too
TODO: Test with local audio
TODO: add better exception handling
TODO: Add logging: http://stackoverflow.com/questions/34588421/how-to-log-to-journald-systemd-via-python

# Nice to haves
TODO: Add hook to automatically update scripts from github
TODO: save wavs as mp3s?
TODO: Replace all other shell commands to pure python too
"""

try:
    # Pin Setup:
    GPIO.setmode(GPIO.BOARD)  # Broadcom pin-numbering scheme

    # Initiate and blink LEDs:
    if LED1PIN:
        GPIO.setup(LED1PIN, GPIO.OUT)
        GPIO.output(LED1PIN, GPIO.LOW)

    if LED2PIN:
        GPIO.setup(LED2PIN, GPIO.OUT)
        GPIO.output(LED2PIN, GPIO.LOW)

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

    def load_playlist(playlist="SoundCloud/Sets/Frank"):
        """
        Change playlist in Mopidy
        TODO: Base it on NFC tags

        # mpc clear
        # mpc ls SoundCloud/Sets/
        """
        # TODO: use control_mpc()
        proc = Popen(['mpc', '-h', 'localhost', '-p', '6600', 'clear', '-q'])

        args = [
            'mpc',
            '-h', 'localhost',
            '-p', '6600',
            'ls', playlist,
        ]
        logger.debug("loading playlist %s", playlist)
        p1 = subprocess.Popen(args, stdout=subprocess.PIPE)
        output, error = p1.communicate()
        # lines = subprocess.check_output(args, shell=True)
        for line in output.split(os.linesep):
            # quotedline = '"%s"' % line
            # print quotedline
            song = Popen(['mpc', 'add', line])

    def nfc_callback(uid):
        """
        Function that decides what to do when an NFC chips is presented, based on the uid of the chip.

        """
        if uid == "0405346A643481":
            load_playlist("SoundCloud/Sets/Frank")
        else:
            load_playlist("SoundCloud/Sets/Test")

        # write playlist info to file
        logger.debug("writing date to %s", NFC_CHIP_DATA_FILE)
        nfc_data = read_nfc_string()
        f = open(NFC_CHIP_DATA_FILE, 'w')
        f.write(nfc_data)
        f.close()

        logger.debug("changed playlist")

    def save_soundcloud_set_datafile(name):
        """
        Copy data file content to sound specific data file.
        If no data file was there, write file for Soundcloud Test set.
        """
        if os.path.isfile(NFC_CHIP_DATA_FILE):
            copyfile(NFC_CHIP_DATA_FILE, name)
        else:
            f = open(NFC_CHIP_DATA_FILE, 'w')
            f.write("SoundCloud/Sets/Test")
            f.close()

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

    def take_picture(name):
        """
        Take a picture with the first available webcam device.
        """
        # proc = Popen(['fswebcam', '-d', '/dev/video1', '-r' , '1280x720', '--no-banner', name])
        proc = Popen(['fswebcam', '-r', '1280x720', '--no-banner', name])

    def record_sound(name):
        """
        Do some audio recording
        e.g. arecord -D plughw:CARD=Device,DEV=0 -f S16_LE -c1 -r44100 -V mono tik2.wav
        """

        # TODO: remove static sound
        # TODO: test piping into lame mp3 encoding
        args = [
            'arecord',
            '-D', 'plughw:CARD=Device,DEV=0',
            '-f', 'S16_LE',
            '-c1',
            '-r44100',
            '-V', 'mono',
            '--process-id-file', RECORDING_PROCESS_ID_FILE,
            name
        ]
        proc = Popen(args)

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
        file = open(pidfile)
        pid = int(file.readline().strip())
        os.kill(pid, signal.SIGINT)

    def control_mpc(action):
        """
        Run mpc commands to control Mopidy Music server.
        """
        logger.debug("MPC %s", action)
        proc = Popen(['mpc', '-h', 'localhost', '-p', '6600', action, '-q'])

    def blink(number, sleep):
        for i in range(0,number):
            GPIO.output(LED1PIN, GPIO.HIGH)
            time.sleep(sleep)
            GPIO.output(LED1PIN, GPIO.LOW)
            time.sleep(sleep)

    def button_feedback():
        """
        Give feedback on button press.
        """
        # buttonSound.play()
        # proc = Popen(['aplay', os.path.join(HOME_DIR, "button.wav")])

        # TODO: make it possible again to play this sound while playing sounds
        # in mopidy

        if LED1PIN:
            blink(1,0.5)

    def button_rec():
        logger.debug("REC button")

        if not check_recording():
            if check_playing():
                control_mpc('stop')
            GPIO.output(LED1PIN, GPIO.HIGH)
            dt = "%s" % (datetime.datetime.now())
            dtp = "%s.jpg" % (dt)
            dts = "%s.wav" % (dt)
            dtset = "%s.setname" % (dt)
            picture_file = os.path.join(MUSIC_DIR, dtp)
            sound_file = os.path.join(MUSIC_DIR, dts)
            soundcloud_set_file = os.path.join(MUSIC_DIR, dtset)
            take_picture(picture_file)
            record_sound(sound_file)
            save_soundcloud_set_datafile(soundcloud_set_file)
        else:
            pass

    def button_prev():
        logger.debug("PREV button")
        if check_playing():
            control_mpc('prev')
            button_feedback()
        else:
            pass

    def button_play():
        logger.debug("PLAY button")
        if not check_playing():
            control_mpc('play')
            button_feedback()
        else:
            pass

    def button_next():
        logger.debug("NEXT button")
        if check_playing():
            control_mpc('next')
            button_feedback()
        else:
            pass

    def button_stop():
        logger.debug("STOP button")
        if check_recording():
            stop_recording()
            GPIO.output(LED1PIN, GPIO.LOW)

        if check_playing():
            control_mpc('stop')
            button_feedback()
        else:
            pass

    def button_pause():
        logger.debug("PAUSE button")
        if check_playing():
            control_mpc('pause')
            button_feedback()
        else:
            pass

    # def mpc_callback_btn1(channel=False):
    #     print "Button pressed (%s)" % channel
    #     # if channel == BUT1PIN and not check_playing():
    #     if not check_playing():
    #         play_sound()
    #         control_mpc('play')
    #
    #     # elif channel == BUT1PIN and check_playing():
    #     else:
    #         play_sound()
    #         control_mpc('pause')
    #         # control_mpc('stop')
    #
    # def mpc_callback_btn2(channel=False):
    #     print datetime.datetime.now()
    #     print "Button pressed (%s)" % channel
    #     # if channel == BUT2PIN and check_playing():
    #     if check_playing():
    #         print "Button 2"
    #         play_sound()
    #         control_mpc('next')
    #
    # def mpc_callback_btn3(channel=False):
    #     print datetime.datetime.now()
    #     print "Button pressed (%s)" % channel
    #     # if channel == BUT3PIN and check_recording():
    #     if check_recording():
    #         print "Button 3"
    #         # it is recording, so stop it
    #         stop_recording()
    #
    #         GPIO.output(LED1PIN, GPIO.LOW)
    #         GPIO.output(LED1PIN, GPIO.HIGH)
    #         time.sleep(1)
    #         GPIO.output(LED1PIN, GPIO.LOW)
    #         play_sound()
    #
    #     # elif channel == BUT3PIN and not check_recording():
    #     else:
    #         print "Button 3"
    #         # not recording, so start :)
    #         # save picture and sound with same name
    #         play_sound()
    #         GPIO.output(LED1PIN, GPIO.HIGH)
    #
    #         # TODO: add little delay?
    #         time.sleep(1)
    #         dt = "%s" % (datetime.datetime.now())
    #         dtp = "%s.jpg" % (dt)
    #         dts = "%s.wav" % (dt)
    #         picture_name = os.path.join(MUSIC_DIR, dtp)
    #         sound_name = os.path.join(MUSIC_DIR, dts)
    #         take_picture(picture_name)
    #         record_sound(sound_name)
    #
    # count = 0
    # prev_inp = 1
    # def button_check(buttonpin):
    #     global prev_inp
    #     global count
    #
    #     if ((not prev_inp) and inp):
    #         count = count + 1
    #         print "Button pressed (%s)" % buttonpin
    #         print count
    #     prev_inp = inp
    #     time.sleep(0.05)


    logger.debug("Starting. Press CTRL+C to exit")
    logger.debug(("Waiting 10 seconds to restart Mopidy.")
    time.sleep(10)
    logger.debug(("Restarting Mopidy and waiting 5 seconds.")
    proc = Popen(['sudo', 'systemctl', 'restart', 'mopidy'])
    time.sleep(5)
    logger.debug(("OK, here we go!")
    if LED1PIN:
        blink(3,0.5)

    # Load initial playlist
    load_playlist()

    # Check for input
    previous_uid = None
    while True:
        if NFC_READER_PRESENT == True:
            try:
                uid = mifare.select()
                if uid and uid != previous_uid:
                    logger.debug("new NFC detected (%s)", uid)
                    previous_uid = uid
                    nfc_callback(uid)
                    # x = 0
                    # bytesRead = []
                    # while True:
                    #         try:
                    #                 blockBytes = mifare.read_block(x)
                    #                 bytesRead.append(blockBytes)
                    #                 x += 4
                    #         except nxppy.ReadError:
                    #                 print("Length: {0}".format(x))
                    #                 break
                    # if bytesRead:
                    #         ba = bytearray(''.join(bytesRead))
                    #         f = open(uid, 'w')
                    #         f.write(ba);
                    #         break
            except nxppy.SelectError:
                pass

        # TODO: Refactor nested if statements
        if BUT1PIN:
            if GPIO.event_detected(BUT1PIN):
                button_play()
        if BUT2PIN:
            if GPIO.event_detected(BUT2PIN):
                button_stop()
        if BUT3PIN:
            if GPIO.event_detected(BUT3PIN):
                button_rec()
        if BUT4PIN:
            if GPIO.event_detected(BUT4PIN):
                pass
        if BUT5PIN:
            if GPIO.event_detected(BUT5PIN):
                pass
        if BUT6PIN:
            if GPIO.event_detected(BUT6PIN):
                pass
        time.sleep(1)

except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly:
    GPIO.cleanup()  # cleanup all GPIO
