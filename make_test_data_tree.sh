#!/bin/bash

# check and process arguments

if [[ $# != 2 ]]; then
    echo 'The script requires two arguments:'
    echo "  The first argument is the name of the root directory of the data tree"
    echo "  The second argument is the name of the directory that will be created for testing the modification scripts"
    echo "Example: $0 /data/feder ~/test_data_tree"
    exit 1
fi

data_root=$1
test_tree=$2

cp_cmd="cp -Rvp"
# refuse to overwrite a directory that already exists
if [[ -a $test_tree ]]; then
    echo "Directory $test_tree already exists."
    echo "Please check that the location is correct. If it is, remove the directory before running this script."
    exit 1
fi

mkdir -p $test_tree || exit 1
$cp_cmd $data_root/SSG $test_tree
$cp_cmd $data_root/data $test_tree
$cp_cmd $data_root/field-trips $test_tree
$cp_cmd $data_root/SSG $test_tree
# only grab a subset of the perham data...
mkdir -p $test_tree/perham/ey-uma-2012-02-12
$cp_cmd $data_root/perham/ey-uma-2012-02-12/ey-uma-02[0-5]R_*.fit $test_tree/perham/ey-uma-2012-02-12
$cp_cmd $data_root/workarea $test_tree

# only grab a subset of the ast390 data directories
mkdir -p $test_tree/ast390
move_these="2013-01-27 2012-05-12"

for d in $move_these; do
    dest=$test_tree/ast390
    mkdir -p $dest
    $cp_cmd $data_root/ast390/$d $dest
done

# we don't need actual archives to test removing them, we just need files with the right extensions
fake_tgz=$(find $data_root -name \*.tgz)
fake_zip=$(find $data_root -name \*.zip)
fakes="$fake_zip $fake_tgz"
for fake in $fakes; do
    base=$(basename $fake)
    dest=$test_tree/ast390/$base
    echo "Creating fake archive $base as $dest"
    touch $dest
done
