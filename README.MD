# Jimmy's Story Engine/ Cassette Recorder and Player (project stormy)

# TODO Nice to have
TODO: Test: Move wav duplicate to separate dir after mp3 download
TODO: Save and upload more relevant info to SoundCloud? (Length, image, location, wifi name, ip, ...; Possibly add standard info on a new location through command line tool?)
TODO: Change name to verhalen
TODO: Get rid of RECORDING_DIR_NAME
TODO: Force upload/ download on some button combination
TODO: Split functions over multiple files and import
TODO: Make it object oriented
TODO: Make it possible to switch to online mode (only use soundcloud)
TODO: Make it possible to have some hybrid mode to save disk space (playlists in mopidy of local and soundcloud files?)
TODO: Make pip requirements file
TODO: Maybe switch to https://github.com/Mic92/python-mpd2
TODO: Replace all other shell commands to pure python too
TODO: Use sound for button feedback?
TODO: Add some hook to automatically update scripts from github maybe? from another git branch

# How to make this work

## Install Raspbian

1. Make a fresh install of Raspbian <https://www.raspberrypi.org/downloads/raspbian/>
2. Start it up and ssh into it

```
ssh pi@raspberrypi.local
```

1. Update firmware

```
sudo rpi-update
```

1. Update and upgrade packages

```
sudo apt-get update
sudo apt-get dist-upgrade
```

## Install Mopidy

1. Follow these instructions: <http://mopidy.readthedocs.io/en/latest/installation/debian/#debian-install>

```
wget -q -O - https://apt.mopidy.com/mopidy.gpg | sudo apt-key add -
sudo wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/jessie.list
sudo apt-get update
sudo apt-get install mopidy
```

1. Enable Mopidy as a service

  ```
  sudo systemctl enable mopidy
  ```

To control or check the service manually:

```
sudo systemctl start mopidy
sudo systemctl stop mopidy
sudo systemctl restart mopidy
sudo systemctl status mopidy
```

Check the logs:

```
cat /var/log/mopidy/mopidy.log
```

## Install Mopidy extensions

```
sudo apt-get install mopidy-spotify
sudo apt-get install mopidy-soundcloud
sudo pip install Mopidy-Spotmop
sudo pip install Mopidy-Moped
sudo pip install Mopidy-WebSettings
```

## Configure Mopidy

```
sudo nano /etc/mopidy/mopidy.conf
```

add:

```
[local]
enabled = true
library = json
media_dir = $XDG_MUSIC_DIR
scan_timeout = 1000
scan_flush_threshold = 100
scan_follow_symlinks = false
excluded_file_extensions =
  .directory
  .html
  .jpeg
  .jpg
  .log
  .nfo
  .png
  .txt
  .setname
  .notuploaded

[http]
enabled = true
hostname = ::
port = 6680
static_dir =
zeroconf = Mopidy HTTP server on $hostname

[mpd]
enabled = true
hostname = ::
port = 6600
password =
max_connections = 20
connection_timeout = 60
zeroconf = Mopidy MPD server on $hostname
command_blacklist = listall,listallinfo
default_playlist_scheme = m3u

[websettings]
enabled = true
musicbox = false
config_file = /etc/mopidy/mopidy.conf

[soundcloud]
auth_token = 1-35204-229958105-3a372e24e3e04a
# auth_token =1-35204-254727818-4e1bde9f2db976
explore_songs = 25
enabled = true

[audio]
mixer = software
mixer_volume = 80
output = alsasink device=hw:1,0
buffer_time =

[stream]
timeout = 10000
```

## Install MPC

```
sudo apt-get install mpc
```

To control manually:

```
mpc play
mpc pause
mpc prev
mpc next
mpc stop
mpc volume 90 (%)
mpc volume +10
mpc volume -10  
mpc seek +10%
mpc ls “SoundCloud/Sets/Frank" | mpc add
```

## Install Player/ Recorder dependencies

```
sudo apt-get install rpi.gpio
sudo apt-get install fswebcam
sudo pip install soundcloud
```

## Change some Raspberry Pi settings

```
sudo raspi-config
```

- Expand Filesystem
- Change password
- Enable SPI under advanced options
- Setup internationalisation options (Language and Timezone)

## Install dependencies for NXP NFC reader

Check <https://www.youtube.com/watch?v=kbt4LFZptPk>

1. Download these files: <https://www.element14.com/community/docs/DOC-65447/l/explore-nfc-software-and-project?ICID=designcenter-devkitnfc-quick>

2.

```
sudo dpkg -i *.deb
sudo pip install nxppy
```

To test

```
explorenfc-basic -k
```

## GIT

```
sudo apt-get install git-core
```

Do this <https://help.github.com/articles/generating-an-ssh-key/>

```
cd /home/pi/
git clone git@github.com:erwinelling/stormy.git
```

To update:

```
cd /home/pi/stormy
git pull
```

## Change hostname

```
sudo nano /etc/hosts
```

Add:

```
127.0.1.1       jimmys
```

```
sudo nano /etc/hostname
```

Change content to:

```
stormy
```

```
sudo /etc/init.d/hostname.sh
sudo reboot
```

From now on:

```
ssh pi@stormy.local
```

## Add public keys

<https://www.raspberrypi.org/documentation/remote-access/ssh/passwordless.md>

## Add cronjob for Soundcloud upload

```
chmod a+x /home/pi/stormy/upload.py
crontab -e
```

Make sure to use crontab and not sudo, so the cronjob will run for user pi.

Add:

```
*/5 * * * * /usr/bin/python /home/pi/stormy/upload.py > /home/pi/stormy/upload.log
```

## Add logs for cron:

```
sudo nano /etc/rsyslog.conf
```

and uncomment the line

```
# cron.*                          /var/log/cron.log
```

After that, you need to restart rsyslog via

```
$ sudo /etc/init.d/rsyslog restart
```

## Run player as a service

As per <http://www.raspberrypi-spy.co.uk/2015/10/how-to-autorun-a-python-script-on-boot-using-systemd/> and Give it the right permissions and enable our unit file as service

```
sudo chmod 644 /home/pi/stormy/machine.service
sudo systemctl enable /home/pi/stormy/machine.service
```

To control or check the service manually:

```
sudo systemctl start machine
sudo systemctl stop machine
sudo systemctl restart machine
sudo systemctl status machine
```

To check logs:

```
cat /var/log/mopidy/mopidy.log
```

## Make downloader WORK
https://github.com/Suyash458/soundcloud-dl

pip install soundcloud_dl





## Setting up audio
USB DEVICE DOES NOT WORK PROPERLY YET


As per http://www.alsa-project.org/main/index.php/Setting_the_default_device

Find your desired card with:

```
cat /proc/asound/cards
```

and then create /etc/asound.conf with following:

```
   defaults.pcm.card 1
   defaults.ctl.card 1
```

Replace "1" with number of your card determined above.

## Logs
Check the logs:

```
cat /var/log/mopidy/mopidy.log
```

## Disable Pulseaudio
https://wiki.archlinux.org/index.php/PulseAudio/Examples#Disabling_pulseaudio_daemon_altogether

# Often used to debug:

sudo systemctl restart mopidy
sudo systemctl stop mopidy
sudo systemctl restart machine
sudo systemctl stop machine
sudo systemctl status machine
sudo nano /etc/mopidy/mopidy.conf
sudo mopidyctl local scan
tail -f /var/log/mopidy/mopidy.log

output = alsasink device=hw:1,0

tail -f /home/pi/stormy/machine.log
tail -f /home/pi/stormy/upload.log
