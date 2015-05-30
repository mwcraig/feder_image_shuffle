#! /bin/bash

dirs=$(find /Volumes/Dark_Matter/feder_processed/staged/201* -type d)

echo "Copying scripts to..."
for d in $dirs
do
    echo "    $d"
    cp 1-whack_image_and_update_overscan.sh delete_imagehw $d
done

echo "Running scripts"
for d in dirs
do
    echo "    Starting $d..."
    bash ./1-whack_image_and_update_overscan.sh
    echo "    Finished $d"
done
