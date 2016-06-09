#!/bin/bash

mount /btrfs-volume /mnt

python src/main.py "/etc/cobalt/config.json"