echo "STARTING directory $(pwd)"
echo "    Deleting IMAGEH and IMAGEW...."
python delete_imagehw.py
echo "    Updating overscan keywords...."
run_patch.py --overscan-only .
echo "Completed directory $(pwd)"
