This repo is likely only of interest to a couple people...but if you have stumbled upon this and want to know more, here you go...

+ Install these packages to run these scripts: `ccdproc msumastro jinja2 github3.py`
+ Download or clone onto a local drive.
+ Run ``data_tree_reorganization.sh`` with a single argument: the root directory of the data tree.
+ Get some coffee; moving ~250GB will take a few minutes.
+ If you want to test the script first, run ``make_test_data_tree.sh`` with no arguments to get a brief description of its instructions and run ``data_tree_reorganization.sh`` on the test tree you create.

## Finding files that missed header patching

``find_unpatched.py`` scans FITS files for the signature of a file that
``run_patch.py``/``patch_headers`` never touched, or only partially patched.
This can happen silently: an unrecognized ``SWCREATE`` value aborts patching
for the rest of a night, but nothing downstream currently notices. It needs
only astropy; if msumastro is installed too, its list of recognized software
versions is used instead of the copy in the script.

Usage:

    python find_unpatched.py [ROOT ...] [--since YYYY-MM-DD] \
        [--output unpatched_files.csv] [--all] [--no-manifest] [--quiet]

With no arguments it scans the default roots, ``/uncalibrated`` and
``/raw/staged`` (matching ``stage_night.sh``). ``--since``
restricts the scan to nights on or after the given date. Only the top level
of a night directory is scanned, matching what ``run_patch.py`` and
``run_triage.py`` touch, so unreadable or hopeless files can be silenced by
moving them into a subdirectory such as ``bad/``.

By default each directory is scanned from the ``Manifest.txt`` that
``run_triage.py --all`` leaves there, which takes seconds for the whole
archive rather than hours. FITS files not listed in the manifest, and
directories with no manifest or with one written without ``--all`` (so
lacking the ``PURGED`` column), fall back to reading the headers. Manifest rows for files no longer on disk are ignored. A manifest
reflects the headers as of the last triage run, so if files were re-patched
without triage running again afterwards, use ``--no-manifest`` to read every
header instead.

The script writes a CSV of the affected files (``--output``, default
``unpatched_files.csv``; ``--all`` includes the ``ok`` files too) and prints
a summary to stdout: totals by status, a table of affected directories
(with any ``SWCREATE`` or ``INSTRUME`` values patching does not recognize),
unpatched-file counts grouped by ``SWCREATE``, and a plain list of night
directories to feed back into ``run_patch.py``. A file is ``unpatched`` if
it has no ``PURGED`` keyword or is missing one of the keywords patching adds
to every file (``JD-OBS``, ``LATITUDE``, ``LST``); the CSV ``note`` column
says which, and flags files with no ``SWCREATE`` or ``IMAGETYP``, which
patching gives up on without recording and a re-run will not fix. Files
reported as ``partial`` (a LIGHT frame with no ``AIRMASS``/``HA``) are the
missing-pointing cases triage already reports; they do not put a night on
the re-run list. Exit status is ``1`` if any ``unpatched`` or unreadable
file was found, ``0`` otherwise, so it is safe to use from cron.


## Recovering nights that missed patching

Do this once the msumastro release that registers the new software version
(and makes ``run_patch.py`` skip, rather than abort on, unrecognized
``SWCREATE`` values) is installed on the server.

1. One-time: create a ``needs patching`` label on the
   ``feder-observatory/processed_images`` GitHub repo. ``stage_night.sh``
   applies it (via ``create_staging_github_issue.py``) to any night that
   produces a ``NEEDS_PATCHING.txt``.

2. Find the affected nights and keep the CSV:

       python /path/to/feder_image_shuffle/find_unpatched.py --output unpatched_files.csv

   The last section of the output lists the night directories to re-run.

3. Re-run patching and triage in each of those directories. These are the
   same commands ``stage_night.sh`` generates, so the results match a normal
   night:

       cd /uncalibrated/YYYY-MM-DD    # or /raw/staged/YYYY-MM-DD
       run_patch.py -v --destination-dir . --object-list https://raw.github.com/feder-observatory/feder-object-list/master/feder_object_list.csv .
       run_triage.py -v --destination-dir . --all .

   Re-patching is safe on files that were already patched: keywords that
   were previously purged are not purged again, and the other keywords are
   simply rewritten. Files that already have a WCS keep it. If
   ``run_patch.py`` skips files because of a software version or instrument
   not yet in ``feder.py`` it exits nonzero and lists them in
   ``NEEDS_PATCHING.txt``; ``run_patch_error.log`` has the details. Note
   that ``run_triage.py`` fails outright on a night that still contains
   such files, so the manifest is not refreshed for that night.

   Nights that were never given astrometry because patching aborted can be
   solved afterwards with the ``run_astrometry.py`` line from that night's
   ``00-header_process_script.sh``.

4. Confirm with a second scan. Triage has just rewritten the manifests, so
   the default (manifest) mode is current, except for nights where triage
   failed; scan those with ``--no-manifest``:

       python /path/to/feder_image_shuffle/find_unpatched.py

5. For nights that still have an open GitHub issue, refresh its labels and
   file lists:

       python update_staging_issue_labels.py -p /raw/staged YYYY-MM-DD
