#!/bin/sh

clean_up() {
	umount /mnt
	kill -TERM "$child" 2>/dev/null
}
trap clean_up SIGHUP SIGINT SIGTERM


mount /btrfs-volume /mnt
python -u src/main.py "/etc/cobalt/config.json" &

child=$!
wait "$child"

