#!/usr/bin/bash

BASE=/data/feder/data
STAGED=$BASE/staged
PROCESSED=$BASE/processed
README_BASE=https://raw.githubusercontent.com/feder-observatory/processed_images/master/nights/

# Remove trailing slash from night if it is present. If this is not done then the rsync later
# on will move the files, not the directory.
night=${1%/}

readme_name=$night-README.md

pushd $STAGED/$night || exit 1

# Grab the README from github
curl -o $readme_name $README_BASE/$readme_name

popd

pushd $BASE || exit 1

# Move the night
mv staged/$night processed/ || exit 1
