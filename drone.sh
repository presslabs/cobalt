#!/bin/sh

dd if=/dev/zero of=btrfs-drone bs=1 count=0 seek=4G

mkfs.btrfs btrfs-drone

mount btrfs-drone /mnt

btrfs quota enable /mnt

btrfs qgroup limit -e 4G /mnt

mkdir -p /etc/cobalt

mount sample/config1 /etc/cobalt

