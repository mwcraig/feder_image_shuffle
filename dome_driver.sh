#!/bin/bash

# STILL NEEDS ACCESS TO GITHUB TOKEN!!

# Script to stage each night as they are taken. It is best to run this mid-day
# i.e. noon-ish to ensure all syncing is done before staging.

source ~/miniconda3/etc/profile.d/conda.sh
conda activate astro310

cd ~/feder_image_shuffle

python check_dome.py
