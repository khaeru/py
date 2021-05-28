#!/bin/sh
kpartx -av /var/lib/libvirt/images/Windows_7_x64.img
mkdir /media/F25053C250538BEB
chown pnk: /media/F25053C250538BEB
#mount -o uid=1000,umask=077 /dev/disk/by-uuid/F25053C250538BEB /media/F25053C250538BEB
mount -o uid=1000,umask=0077,fmask=0177 /dev/dm-1 /media/F25053C250538BEB
