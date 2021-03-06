#!/bin/sh
# Configure a new Ubuntu machine
#
# Some parts of this script might be better to run manually.
#
# Preceding steps required:
#
# 1. Add MIT SECURE wireless network, and register on MIT Ethernet network.
# 2. $ ssh-keygen -t rsa -b 4096 -C "mail@paul.kishimoto.name -- khaeru-laptop"
# 3. $ cat .ssh/id_rsa.pub
# 4. Log in to https://github.com using 2FA and add the new key.
# 5. # apt install git
# 6. git clone git@github.com:khaeru/scripts.git vc/scripts

clone () {
  # FIXME this fails for Documents/pub
  if [ -z "$2" ]; then
    TARGET=`basename $1`
  else
    TARGET=$2
    mkdir -p vc/`dirname $TARGET`
  fi
  git clone $3 git@github.com:$1.git vc/$TARGET
}

install_set () {
  xargs -a $DF/apt/install.$1 sudo apt install --no-install-recommends
}

# Tidy contents of default desktop
rm -f examples.desktop
rmdir Desktop Downloads Public Templates Videos
mv Pictures Image
mkdir -p Documents

# Clone personal dotfiles

DF=vc/dotfiles
clone khaeru/dotfiles
# Install symlinks to dotfiles
vc/dotfiles/install.sh
# Source newly-symlinked .profile
. ~/.profile

# Add software sources

# PPA keys for
# - flacon
# - Google Chrome
# - Google gcsfuse
# - keybase
# - yubico
# - git-lfs
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys \
  f2a61fe5 \
  d38b4796 \
  a7317b0f \
  656d16c7 \
  32cba1a9 \
  d59097ab
# Install custom ppa.list from dotfiles
sudo install --mode=644 --owner=root $DF/apt/ppa.list \
  /etc/apt/sources.list.d/ppa.list
# Enable Ubuntu's partner repositories
sudo sed -E -i 's/^# (deb .* partner)/\1/' /etc/apt/sources.list
# Update package lists including new sources
sudo apt update

# Install packages
install_set base

# Packages from snaps
sudo snap install atom skype --classic

# R (before Python in order to install r-base-dev, needed to compile rpy2)
install_set R
Rscript - <<EOF
install.packages(
  scan('$DF/R/install', character()),
  repos='https://cloud.r-project.org'
  )
EOF

# Python
install_set python
pip3 install --user --no-deps --upgrade --requirement $DF/pip3/install

# Purge unwanted packages
xargs -a $DF/apt/purge sudo apt purge
sudo apt autoremove --purge
sudo apt clean

# Configure software

# Atom: install Atom packages
sed -n -E 's/^  "(.*)"/\1/p' $DF/atom/packages.cson | xargs apm install

# ddclient: install own configuration
sudo install --mode=600 --owner=root $DF/ddclient.conf /etc/ddclient.conf

# GAMS
# TODO install GAMS itself
# Install GAMS Python API
install-gams-api 24.9.1 _36 pip3 --user

# Gnome Shell
# Install extra extensions from website
# - CoverFlow Alt-Tab
# - Activities Configurator
clone NicolasBernaerts/ubuntu-scripts.git other/ubuntu-scripts
install -m 755 vc/other/ubuntu-scripts/ubuntugnome/gnomeshell-extension-manage \
  .local/bin/
gnomeshell-extension-manage --install --extension-id 97
gnomeshell-extension-manage --install --extension-id 358

# Gnome: load settings
dconf load / < $DF/dconf.txt

# Gnome Terminal: use 'Solarized' colour scheme
clone Anthony25/gnome-terminal-colors-solarized
vc/gnome-terminal-colors-solarized/install.sh <<EOF
1
1
YES
1
EOF
rm -rf dircolors vc/gnome-terminal-colors-solarized

# Latexmk
install-latexmk

# Taskwarrior
mkdir -p $HOME/.local/share/task

# Clone git repositories
clone khaeru/17.310j-fa17
clone khaeru/blog paul.kishimoto.name
clone khaeru/bibliography Documents/reference
clone khaeru/data
clone khaeru/easi
Rscript -e "devtools::install_local('vc/easi')"

clone khaeru/gb2260
pip3 install --user --editable vc/gb2260/

clone khaeru/notes
clone khaeru/publications Documents/pub --recurse-submodules
clone khaeru/py-gdx
pip3 install --user --editable vc/py-gdx/

clone khaeru/tex tex --recurse-submodules
clone khaeru/trb-adc70 trbenergy.org

clone mit-jp/cecp-db
clone mit-jp/cge-workshop mit-jp/cge-workshop
clone mit-jp/cgem mit-jp/cgem
clone mit-jp/crem
clone mit-jp/eppa5 eppa/5
clone mit-jp/eppa6 eppa/6
clone mit-jp/fleet-model

clone transportenergy/database item/database
clone transportenergy/item2-data item/item2-data
clone transportenergy/item2-scripts item/item2-scripts
clone transportenergy/transportenergy.org item/transportenergy.org

clone andreafabrizi/Dropbox-Uploader other/dropbox-uploader
clone ralphbean/bugwarrior other/bugwarrior "--branch develop"
clone khaeru/pelican-alias other/pelican-alias
clone khaeru/pelican-cite other/pelican-cite
clone getpelican/pelican-plugins other/pelican-plugins --recursive
clone getpelican/pelican-themes other/pelican-themes --recursive

# Clean up extra files that may have been created in $HOME
rm -rf .atom .bash_history .compiz .lesshst .nano .task .taskrc
