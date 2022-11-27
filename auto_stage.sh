#!/bin/bash

# STILL NEEDS ACCESS TO GITHUB TOKEN!!

# Script to stage each night as they are taken. It is best to run this mid-day
# i.e. noon-ish to ensure all syncing is done before staging.

source ~/miniconda3/etc/profile.d/conda.sh
conda activate astro310
conda info

cd ~/feder_image_shuffle

# stage the most recent night only

now=$(date -I)

export PATH="/usr/local/astrometry/bin:$PATH"
echo PATH is $PATH
echo solve-field at $(which solve-field)

bash stage_night.sh 7 &>> run_staging_$now.txt

