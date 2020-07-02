# mopidy-mixcloudsimple
This is simple mixcloud backend for Mopidy v3.

It uses [youtube-dl](https://github.com/ytdl-org/youtube-dl) in the background to access Mixcloud.

# install
```
cd ~
git clone https://github.com/magcode/mopidy-mixcloudsimple.git
sudo python3 pip install -e mopidy-mixcloudsimple
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
