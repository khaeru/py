#!/bin/sh
clone () {
  if [ -z "$2" ]; then
    TARGET=`basename $1`
  else
    TARGET=$2
    mkdir -p vc/`dirname $TARGET`
  fi
  git clone $3 git@github.com:$1.git vc/$TARGET
}

clone khaeru/dotfiles
vc/dotfiles/install.sh
dconf load / < vc/dotfiles/dconf.txt
gconftool-2 --set --type bool /apps/nautilus/preferences/desktop_is_home_dir true

rm -f Examples
rmdir Desktop Downloads Public Templates Videos
mv Pictures Image
mkdir -p Documents vc/eppa

clone khaeru/blog
clone khaeru/cjklib
clone khaeru/gb2260
clone khaeru/notes
git clone git@github.com:khaeru/publications.git Documents/pub
clone khaeru/py-gdx
clone khaeru/tex
clone khaeru/trb-adc70

clone mit-jp/cecp-db
clone mit-jp/cgem
clone mit-jp/crem
clone mit-jp/eppa5 eppa/5
clone mit-jp/eppa6 eppa/6
clone mit-jp/fleet-model
clone mit-jp/jp-report-tex

clone andreafabrizi/Dropbox-Uploader other/dropbox-uploader
clone Hightor/gitinfo2 other/gitinfo2
clone matze/mtheme other/mtheme
clone Nitron/pelican-alias other/pelican-alias
clone khaeru/pelican-cite other/pelican-cite
clone getpelican/pelican-plugins other/pelican-plugins --recursive
clone getpelican/pelican-themes other/pelican-themes --recursive
git clone git://git.code.sf.net/p/pgfplots/code vc/other/pgfplots

# Packages
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys \
  5ed1d082 \  # claws-mail
  f2a61fe5 \  # flacon
  f8214acd \  # lyx-devel
  cedf0f40 \  # musicbrainz-developers
  eea14886 \  # webupd8team
  32cba1a9 \  # yubico
  8f7df243 \  # zim
  d59097ab    # git-lfs
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -

sudo cp vc/dotfiles/apt/ppa.list /etc/apt/sources.list.d/
# TODO edit /etc/apt/sources.list to uncomment the line:
#  deb http://archive.canonical.com/ubuntu xenial partner
sudo apt update
sudo apt install --no-install-recommends $(cat vc/dotfiles/apt/install | tr "\n" " ")
sudo apt purge $(cat vc/dotfiles/apt/purge | tr "\n" " ")
# TODO edit /etc/apt/sources.list.d/ppa.list to remove the line for Google Chrome

# Manually install: anki

# Atom
apm install --packages-file vc/dotfiles/atom.packages

# Python
pip2 install --user --no-deps --upgrade --requirement vc/dotfiles/python2.packages
pip3 install --user --no-deps --upgrade --requirement vc/dotfiles/python3.packages

# ddclient TODO

# Gnome-terminal
git clone git@github.com:Anthony25/gnome-terminal-colors-solarized.git
gnome-terminal-colors-solarized/install.sh <<EOF
1
1
YES
EOF
rm -rf gnome-terminal-colors-solarized
