#!/bin/bash

# check and process arguments

if [[ $# != 1 ]]; then
    echo 'The script requires one argument: the name of the root directory of the data tree'
    echo 'On physics this root is /data/feder'
    exit 1
fi

data_root=$1

##### FUNCTION DEFINTITIONS

# function to color code text output

color_text () {
    endColor=$'\e[0m'
    color=$1
    msg=$2
    case $1 in
        "red" )
        startColor=$'\e[1;31m'
        ;;
        "green" )
        startColor=$'\e[32m'
        ;;
        "blue" )
        startColor=$'\e[1;34m'
        ;;
        * )
        echo "I do not know the color $1"
        exit 1
        ;;
    esac
    result="$startColor$msg$endColor"
    echo -e $result
}

# function to set permissions on newly created directories

set_write_permissions () {
    directory=$1   # this $1 is the first argument to the function, not the first command line arg...
    chown :feder $directory || color_text red "Group ownership of directory $directory not changed (should be feder group)"
    chmod ug+w $directory || color_text red "User+group write permissions of directory $directory not changed (should be ug+w)"
    chmod o-w $directory || color_text red "Other write permissions of directory $directory not changed (should be o-w)"    
}

# makes declaring a win easier...

success () {
    color_text green "      Succeeded"
}

#### END FUNCTION DEFITIONS

#### CHECK WHETHER THE DATA ROOT IS ONE OF THE SACRED_PATHS

# Any paths list as part of sacred_paths will be checked against $data_root
# if there is a match, the script aborts
sacred_roots="/data/feder /Volumes/Dark_Matter/feder /home/faculty/matt.craig/sacred /Users/matthewcraig/sacred"

for path in $sacred_roots; do
    if [[ "$data_root" -ef "$path" ]]; then
        color_text red "I REFUSE TO TOUCH ACTUAL DATA DIRECTORIES RIGHT NOW"
        exit 1
    fi
done


### BEGIN IMPLEMENTATION OF ACTUAL DATA MOVEMENT

# implement item 1 from email:
#
#   Remove the folder /feder/data/perham [contains reduced images related to an outreach project a couple years ago.]

color_text blue "Attempting to remove perham directory"
rm -rf $data_root/perham && success || color_text red "Unable to remove perham directory"

# implement item 2 from email:
#
#    Archive then remove the folder /data/feder/field-trips and download 

# Archive...
field_trip_dir_name=field-trips
field_trips=$data_root/$field_trip_dir_name
color_text blue "Archiving directory $field_trips"
pushd $data_root && ( tar czf $data_root/field-trips.tgz $field_trip_dir_name && success || color_text red "Archive of field-trips not created" ) && popd
color_text blue "Removing directory $field_trips"
rm -rf $field_trips && success || color_text red "Unable to remove directory $field_trips"

# Downloading will need to be done manually

# implement item 3 from email:
#
#   Remove the directory /data/feder/workarea AFTER sending any data in those directories to the people whose names are on them

# Will actually create archive of each in the root directory then delete the directories

work_area=$data_root/workarea
work_dirs=$data_root/workarea/*

for dir in $work_dirs; do
    color_text blue "Archiving work area directory $dir"
    current_target=$(basename $dir)
    archive_name="$current_target.tgz"
    #color_text blue "$data_root/$archive_name"
    pushd $work_area || continue
    ( tar czf $data_root/$archive_name.tgz $current_target && rm -rf $current_target ) && success || color_text red "Creating archive of $dir failed; directory not removed"
    popd
done
color_text blue "Removing old work directory $work_area"
rm -rf $work_area && success || color_text red "Could not remove $work_area"

# implement item NOT IN EMAIL:
#
#   Remove tar archives in the current ast390 top level

color_text blue "Removing any archives in the top level of ast390"
rm $data_root/ast390/*.zip $data_root/ast390/*.tgz && success || color_text red "Unable to remove archives from $data_root/ast390"

# implement item 4a from email:
#
#   Move everything currently in /data/feder/ast390 to /data/feder/data/raw

source_directory=$data_root/ast390
raw_directory=$data_root/data/raw
color_text blue "Creating directory to hold raw data: $raw_directory"
mkdir -p $raw_directory && success || exit 1

color_text blue "Moving existing data from $source_directory to $raw_directory"
mv $source_directory/* $raw_directory && success || color_text red "Unable to move existing data to $raw_directory"

color_text blue "Removing old raw directory $source_directory"
# LEAVE THIS AS RMDIR so that it will fail if the directory is not empty
rmdir $source_directory && success || color_text red "Did not remove directory $source_directory"

# implement item 4b from email:
#
#   Change file permissions so that no one has write permission

color_text red "====> Run this command as sudo to change permissions: chmod ugo-w -R $raw_directory"

# implement item 5 from email:
#
#   Create a directory /data/feder/data/upload that has write access for feder_users. 

upload_dir=$data_root/data/upload
color_text blue "Creating directory to store uploads: $upload_dir"

mkdir -p $upload_dir && success || exit 1
color_text blue "Setting permissions on upload_dir"
set_write_permissions $upload_dir && success # feedback taken care of in function

# implement item 6 from email:
#
#   Create a directory /data/feder/data/processed that will contain a mirror of what is in /data/feder/data/raw but with header processing done 

processed_dir=$data_root/data/processed
color_text blue "Creating directory for processed files: $processed_dir"
mkdir -p $processed_dir && success || exit 1
color_text blue "Setting permissions for $processed_dir"
set_write_permissions $processed_dir && success # feedback taken care of in function

# implement item 7 from email:
#
#   Move the folder /data/feder/SSG to /data/feder/data/SSG

color_text blue "Moving SSG directory"
mv $data_root/SSG $data_root/data/SSG && success || color_text red "Unable to move the SSG directory"
