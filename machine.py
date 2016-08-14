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

# Pin Definitons:
# pwmPin = 12 # Broadcom pin 18 (P1 pin 12)
# ledPin = 16 # Broadcom pin 23 (P1 pin 16)
# but1Pin = 11 # Broadcom pin 17 (P1 pin 11)
# but2Pin = 13
# but3Pin = 15


# Nieuwe pins voor met NXP bordje
# ground = 39
led1Pin = 32 # Broadcom pin 18 (P1 pin 12)
led2Pin = 36 # Broadcom pin 23 (P1 pin 16)
but1Pin = 31 # Broadcom pin 17 (P1 pin 11)
but2Pin = 33
but3Pin = 35
but4Pin = False
but5Pin = False
homedir = "/home/pi/stormy/"
musicdir = "/home/pi/Music/"
NFC_READER_PRESENT = False
STOP_CHARACTER = "STOP"
recording_process_id_file = os.path.join(homedir, "recprocess.pid")

"""
TODO: Put everything on Github, possibly branched, and with hook
TODO: set volume 100% alsamixer
TODO: turn off spotify for faster loading?
TODO: check if mpd server is ready (takes a while: ~2mins)
TODO: load playlists from soundcloud!
TODO: load this script at startup
TODO: save mp3s
TODO: check if i can stop the static
TODO: play sounds earlier/ faster
TODO: change sounds for buttons
TODO: add more exceptions
TODO: add some logging?
TODO: change uploadscript to add files to right playlist
"""


try:
    # Pin Setup:
    GPIO.setmode(GPIO.BOARD) # Broadcom pin-numbering scheme
    GPIO.setup(led2Pin, GPIO.OUT)
    GPIO.setup(led1Pin, GPIO.OUT)

    GPIO.setup(but1Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Button pin set as input w/ pull-up
    GPIO.setup(but2Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Button pin set as input w/ pull-up
    GPIO.setup(but3Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Button pin set as input w/ pull-up

    # Initial state for LEDs:
    GPIO.output(led2Pin, GPIO.LOW)
    GPIO.output(led1Pin, GPIO.LOW)

    # Initiate NFC reader:
    mifare = nxppy.Mifare()

    def write_nfc_string(str):
        nr = 10
        for i in xrange(0, len(str), 4):
            uid = mifare.select()
            # print "id: %s, %s" % (nr, str[i:(i+4)])
            mifare.write_block(nr, str[i:(i+4)])
            nr += 1
        mifare.write_block(nr, STOP_CHARACTER)


    def read_nfc_string():
        max_block = 1000  # if "STOP" is not found, when should we stop?
        block = 10
        output = ""
        stop = False
        count = 0
        while stop is False:
            data = mifare.read_block(block)
            if data == STOP_CHARACTER or block > max_block:
                stop = True
            else:
                output += data
            block += 1
        return output
        
    def load_playlist(playlist="SoundCloud/Sets/Frank"):
        """
        Change playlists with NFC tags?
        """
        # TODO: use control_mpc()
        proc = Popen(['mpc', '-h', 'localhost', '-p', '6600', 'clear', '-q'])

        args = [
            'mpc',
            '-h', 'localhost',
            '-p', '6600',
            'ls', playlist,
        ]
        p1 = subprocess.Popen(args, stdout=subprocess.PIPE)
        output, error = p1.communicate()
        # lines = subprocess.check_output(args, shell=True)
        for line in output.split(os.linesep):
            # quotedline = '"%s"' % line
            # print quotedline
            song = Popen(['mpc', 'add', line])

        # clear current playlist
        #mpc clear 
        
        # add soundcloud playlist
        #mpc add soundcloud:set-...
        # nope, this gives errors, check this:
        # vim /var/log/mopidy/mopidy.log
        # and somehow find out how to add the right playlist
        # mpc ls SoundCloud/Sets/
        
    def nfc_callback(uid):        
        if uid == "0405346A643481":
            load_playlist("SoundCloud/Sets/Frank")
        else:
            load_playlist("SoundCloud/Sets/Test")
        print "changed playlist"
        
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
            print "Playing? No"
            return False
        else:
            print "Playing? Yes"
            return True
        
    def take_picture(name):
        """
        Take a picture with the first available webcam device.
        """
        # proc = Popen(['fswebcam', '-d', '/dev/video1', '-r' , '1280x720', '--no-banner', name])
        proc = Popen(['fswebcam', '-r' , '1280x720', '--no-banner', name])
    
    def record_sound(name):
        """
        Do some recording
        Also take a picture
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
            '--process-id-file', recording_process_id_file,
            name
        ]
        proc = Popen(args)

    def check_recording():
        """
        Helper function to see whether something is being recorded.
        """
        if os.path.isfile(recording_process_id_file):
            return True
            print "Recording? Yes"
        else:
            return False
            print "Recording? No"
                    
    def stop_recording():
        """
        Kill the recording process.
        """
        pidfile = os.path.join(homedir, recording_process_id_file)
        file = open(pidfile)
        pid = int(file.readline().strip())
        os.kill(pid, signal.SIGINT)
        
    def control_mpc(action):
        """
        Run mpc commands to control Mopidy Music server.
        """
        print "MPC %s" % action
        proc = Popen(['mpc', '-h', 'localhost', '-p', '6600', action, '-q'])
        GPIO.output(led2Pin, GPIO.HIGH)
        # proc.wait()
        time.sleep(1)            
        GPIO.output(led2Pin, GPIO.LOW)

    def play_sound():
        """
        Play a button sound.
        """
        # buttonSound.play()
        # proc = Popen(['aplay', os.path.join(homedir, "button.wav")])
        
        #TODO: make it possible again to play this sound while playing sounds in mopidy
        pass


    def button_rec():
        print "REC button"
        
        if not check_recording():
            if check_playing():
                control_mpc('stop')
            GPIO.output(led1Pin, GPIO.HIGH)
            dt = "%s" % (datetime.datetime.now())
            dtp = "%s.jpg" % (dt)
            dts = "%s.wav" % (dt)
            picture_name = os.path.join(musicdir, dtp)
            sound_name = os.path.join(musicdir, dts)
            take_picture(picture_name)
            record_sound(sound_name)
        else:
            pass
        
    def button_prev():
        print "PREV button"
        if check_playing():
            control_mpc('prev')
        else:
            pass
        
    def button_play():
        print "PLAY button"
        if not check_playing():
            control_mpc('play')
        else:
            pass
        
    def button_next():
        print "NEXT button"
        if check_playing():
            control_mpc('next')
        else:
            pass        
        
    def button_stop():
        print "STOP button"
        if check_recording():
            stop_recording()
            GPIO.output(led1Pin, GPIO.LOW)
            
        if check_playing():
            control_mpc('stop')
        else:
            pass
                        
    # def mpc_callback_btn1(channel=False):
    #     print "Button pressed (%s)" % channel
    #     # if channel == but1Pin and not check_playing():
    #     if not check_playing():
    #         play_sound()
    #         control_mpc('play')
    #
    #     # elif channel == but1Pin and check_playing():
    #     else:
    #         play_sound()
    #         control_mpc('pause')
    #         # control_mpc('stop')
    #
    # def mpc_callback_btn2(channel=False):
    #     print datetime.datetime.now()
    #     print "Button pressed (%s)" % channel
    #     # if channel == but2Pin and check_playing():
    #     if check_playing():
    #         print "Button 2"
    #         play_sound()
    #         control_mpc('next')
    #
    # def mpc_callback_btn3(channel=False):
    #     print datetime.datetime.now()
    #     print "Button pressed (%s)" % channel
    #     # if channel == but3Pin and check_recording():
    #     if check_recording():
    #         print "Button 3"
    #         # it is recording, so stop it
    #         stop_recording()
    #
    #         GPIO.output(led1Pin, GPIO.LOW)
    #         GPIO.output(led1Pin, GPIO.HIGH)
    #         time.sleep(1)
    #         GPIO.output(led1Pin, GPIO.LOW)
    #         play_sound()
    #
    #     # elif channel == but3Pin and not check_recording():
    #     else:
    #         print "Button 3"
    #         # not recording, so start :)
    #         # save picture and sound with same name
    #         play_sound()
    #         GPIO.output(led1Pin, GPIO.HIGH)
    #
    #         # TODO: add little delay?
    #         time.sleep(1)
    #         dt = "%s" % (datetime.datetime.now())
    #         dtp = "%s.jpg" % (dt)
    #         dts = "%s.wav" % (dt)
    #         picture_name = os.path.join(musicdir, dtp)
    #         sound_name = os.path.join(musicdir, dts)
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


    # Load initial playlist
    load_playlist()

    GPIO.add_event_detect(but1Pin, GPIO.FALLING, bouncetime=200)
    GPIO.add_event_detect(but2Pin, GPIO.FALLING, bouncetime=200)
    GPIO.add_event_detect(but3Pin, GPIO.FALLING, bouncetime=200)
    
    # Blink both leds when started
    GPIO.output(led1Pin, GPIO.HIGH)        
    GPIO.output(led2Pin, GPIO.HIGH)        
    time.sleep(1)            
    GPIO.output(led1Pin, GPIO.LOW)
    GPIO.output(led2Pin, GPIO.LOW)
    print("Here we go! Press CTRL+C to exit")
    
    previous_uid = None
    while True:
        if NFC_READER_PRESENT == True:
            try:
                uid = mifare.select()
                print uid
                if uid and uid != previous_uid:
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

        if GPIO.event_detected(but1Pin):
            button_play()
        if GPIO.event_detected(but2Pin):
            button_stop()
        if GPIO.event_detected(but3Pin):        
            button_rec()
        time.sleep(1)

except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
    GPIO.cleanup() # cleanup all GPIO