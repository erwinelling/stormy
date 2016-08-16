# Jimmy’s Story Engine/ Cassette Recorder and Player (project stormy)

## Install Raspbian

1. Make a fresh install of Raspbian https://www.raspberrypi.org/downloads/raspbian/
2. Start it up and ssh into it

```
ssh pi@raspberrypi.local
```

3. Update firmware

```
sudo rpi-update
```

4. Update and upgrade packages

```
sudo apt-get update
sudo apt-get dist-upgrade
```

## Install Mopidy

1. Follow these instructions: http://mopidy.readthedocs.io/en/latest/installation/debian/#debian-install

```
wget -q -O - https://apt.mopidy.com/mopidy.gpg | sudo apt-key add -
sudo wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/jessie.list
sudo apt-get update
sudo apt-get install mopidy
```

2. Enable Mopidy as a service
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
auth_token =  1-35204-229958105-3a372e24e3e04a
explore_songs = 25

[audio]
mixer = software
mixer_volume =
output = alsasink
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

## Install dependencies for NXP NFC reader
Check https://www.youtube.com/watch?v=kbt4LFZptPk

1. Download these files:
https://www.element14.com/community/docs/DOC-65447/l/explore-nfc-software-and-project?ICID=designcenter-devkitnfc-quick

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

Do this https://help.github.com/articles/generating-an-ssh-key/

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
jimmys
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
https://www.raspberrypi.org/documentation/remote-access/ssh/passwordless.md

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

# Run player as a service
Give it the right permissions and enable our unit file as service
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
