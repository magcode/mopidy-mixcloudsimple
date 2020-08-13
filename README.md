# mopidy-mixcloudsimple
This is simple Mixcloud backend for [Mopidy V3](https://github.com/mopidy/mopidy).
It uses [youtube-dl](https://github.com/ytdl-org/youtube-dl) in the background to access Mixcloud.

It gives you quick access to the casts of the accounts you follow. It also provides the "New Shows" stream as known from the Mixcloud website.

# install
```
cd ~
git clone https://github.com/magcode/mopidy-mixcloudsimple.git
sudo python3 pip install -e mopidy-mixcloudsimple
# you can also try 'sudo pip3 install -e mopidy-mixcloudsimple' in case the last command does not work
```
# uninstall
```
cd ~/mopidy-mixcloudsimple
sudo python3 setup.py develop -u
```
# configuration in mopidy.conf
```
[mixcloudsimple]
enabled = true
account = <your mixcloud account id>
