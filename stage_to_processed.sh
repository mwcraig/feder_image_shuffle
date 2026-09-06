#!/usr/bin/bash

STAGED=/raw/staged
PROCESSED=/uncalibrated
README_BASE=https://raw.githubusercontent.com/feder-observatory/processed_images/main/nights/

# Remove trailing slash from night if it is present. If this is not done then the rsync later
# on will move the files, not the directory.
night=${1%/}

readme_name=$night-README.md

pushd $STAGED/$night || exit 1

# Grab the README from github
wget $README_BASE/$readme_name

popd

pushd $PROCESSED || exit 1

# Move the night
mv $STAGED/$night . || exit 1
