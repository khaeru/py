#!/bin/sh
umount /media/F25053C250538BEB
rmdir /media/F25053C250538BEB
kpartx -dv /var/lib/libvirt/images/Windows_7_x64.img
