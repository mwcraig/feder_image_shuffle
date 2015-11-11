#!/bin/bash

#
# Move a night from upload to staged, creating and running the standard header
# processing script.
#

# Set root directory once so that it doesn't need to be repeated.
ROOT_DIR='/Users/mcraig/Documents/Data/feder-images/esne-bide-fake'

# Set to the directory that should be checked for new data.
SOURCE_ROOT="$ROOT_DIR/upload"

# Set to the directory where processed data should land. Data will be placed
# in a subfolder of this directory.
STAGE_ROOT="$ROOT_DIR/staged"

# Set to the directory in which the data might have landed after staging.
# If night exists in this directory already then the night will not be
# reprocessed.
PROCESS_ROOT="$ROOT_DIR/processed"

# Base URL for jpeg image gallery on physics server
BASE_GALLERY_URL=http://physics.mnstate.edu/feder_gallery/

# rsync location of galleries
RSYNC_GALLERY_DESTINATION='matt.craig@physics:/data/feder/gallery'

# Set to object list on github.
GITHUB_OBJECT_LIST=https://raw.github.com/mwcraig/feder-object-list/master/feder_object_list.csv

# Check whether any nights need to be processed.
nights_to_process=$(diff $SOURCE_ROOT $STAGE_ROOT | grep "Only in $SOURCE_ROOT" | grep -o -e '20[0-9][0-9]-[01][0-9]-[0-3][0-9]' | sort -r)

cwd=$PWD

# Raise error immediately if the github token is not set.
if [ -z $GITHUB_TOKEN ]; then echo "Set GITHUB_TOKEN before running."; exit 1; fi

# Loop over nights to be processed.
for night in $nights_to_process; do
    # Skip if it looks like this has already been processed.
    if [ -d "$PROCESS_ROOT/$night" ]; then
        echo "Skipping night $night because already in $PROCESS_ROOT"
        continue
    fi

    current_stage=$STAGE_ROOT/$night
    current_source=$SOURCE_ROOT/$night

#   Create destination directory in staged
    mkdir $current_stage || exit 1

#   Change to that directory.
    cd $current_stage

#   Use run_standard_header_process.py --scripts-only to make processing script
    run_standard_header_process.py -o $GITHUB_OBJECT_LIST --scripts-only --dest-root .  $current_source

#   Add "00-"" to the front of the script name. Allows scripts to be ordered.
    script_name=$(ls *.sh)
    new_script_name="00-$script_name"
    mv $script_name $new_script_name

#   Run processing script
    bash $new_script_name || exit 1

#   Trigger creation of github issue(s)?
    cd $cwd
    python create_staging_github_issue.py -p $current_stage $night

#   Make me some jpegs, please...
    jpeg_storage=jpegs/$night
    mkdir -p $jpeg_storage
    python make_images.py $current_stage $jpeg_storage

#   ...and a web page to display those jpegs!
    python make_viewer_pages.py --base-url $BASE_GALLERY_URL/$night $current_stage > $jpeg_storage/index.html
    cp magnific-popup.css jquery.magnific-popup.js $jpeg_storage

#   Now push the gallery to the server, making extra sure that $jpeg_storage
#   does not have a trailing slash.
    rsync -e ssh -av ${jpeg_storage%/} $RSYNC_GALLERY_DESTINATION
done
