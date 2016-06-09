#!/bin/bash

root_path="$(pwd)/../btrfs"
echo "$root_path"

mkdir "$root_path"
cd "$root_path"

for i in {1..3}; do
    # create file
    dd if=/dev/zero of="root$i" bs=1 count=0 seek=1G

    # make filesystem
    sudo mkfs.btrfs "root$i"

    # create mount point folder
    mkdir "$i"

    # mount
    sudo mount "root$i" "$i"

    # enable quotas
    sudo btrfs quota enable "$i"

    # attach quota
    sudo btrfs qgroup limit -e 1G "$i"
done

# restore current dir
cd -