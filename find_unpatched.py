"""
Find FITS files that msumastro's ``run_patch.py`` / ``patch_headers`` never
patched, or only partially patched, and report them. A file is ``unpatched``
if it lacks ``PURGED`` or any of the keywords patching adds to every file;
``partial`` if it is a LIGHT frame without pointing keywords, which triage
already reports as ``NEEDS_POINTING_INFO.txt``.

Needs only astropy.io.fits, so it runs whether or not msumastro is
installed (if it is, its list of recognized software is used). By default each directory is read from the
``Manifest.txt`` that ``run_triage.py --all`` writes there; files missing
from the manifest, and directories without one, fall back to the FITS
headers. HISTORY cards are deliberately ignored: the current msumastro writes
its ``patch_headers`` HISTORY lines before deciding whether it can patch a
file, and an old ``FILE NOT PATCHED`` line survives a later re-patch.

See the README section "Finding files that missed header patching" for the
output format and the recovery procedure. Exit status is 1 if any file is
unpatched or unreadable, else 0.
"""

import argparse
import csv
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

from astropy.io import fits

# Same roots as stage_night.sh.
DEFAULT_ROOTS = ['/uncalibrated', '/raw/staged']

FITS_EXTENSIONS = ('.fit', '.fits', '.fts')
NIGHT_RE = re.compile(r'^20\d\d-[01]\d-[0-3]\d$')

# Keywords patch_headers adds to every file, and to LIGHT frames only.
ALWAYS_KEYS = ('JD-OBS', 'LATITUDE', 'LST')
LIGHT_KEYS = ('AIRMASS', 'HA')
NEEDED_KEYS = ALWAYS_KEYS + LIGHT_KEYS + ('PURGED', 'IMAGETYP', 'SWCREATE',
                                         'INSTRUME', 'CTYPE1')

# The SWCREATE values patch_headers recognizes. Taken from the installed
# msumastro when there is one; the literal mirrors the fits_name lists in
# msumastro/header_processing/feder.py and is the fallback otherwise.
KNOWN_SWCREATE = {
    'MaxIm DL Version 4.10',
    'MaxIm DL Version 5.21 130912 01A17',
    'MaxIm DL Version 5.21 120829 2R1M0',
    'MaxIm DL Version 5.23 130912 01A17',
    'MaxIm DL Version 5.15',
    'MaxIm DL Version 5.14',
    'MaxIm DL Version 6.16 190601 00KPP',
    'MaxIm DL Version 6.17 190601 00KPP',
    'MaxIm DL Version 6.18 190601 00KPP',
    'MaxIm DL Version 6.27 220525 26KU2',
    'MaxIm DL Version 6.29 220525 26KU2',
    'MaxIm DL Version 6.30 220525 26KU2',
    'MaxIm DL Version 6.30 240628 2HVXS',
    'MaxIm DL Version 6.50 240628 2HVXS',
    'MaxIm DL Version 7.1.4.0 260709 07593',
    'SBIG Win CCDOPS Version 5.47 Build 6-NT',
    'Celestron AstroFX V1.06',
}
# Likewise for INSTRUME; patch_headers refuses files from an unknown camera.
KNOWN_INSTRUME = {
    'Apogee Alta', 'Apogee USB/Net', 'SBIG ST-7', 'Celestron Nightscape 10100',
    'Apogee Aspen CG16M', 'AspenCG16',
}
try:
    from msumastro.header_processing.feder import Feder
    KNOWN_SWCREATE = set(Feder().software)
    KNOWN_INSTRUME = set(Feder().instruments)
except ImportError:
    pass


def values_from_header(header):
    """Keyword -> string value for the keywords classification looks at."""
    return {key: str(header[key]) for key in NEEDED_KEYS if key in header}


def values_from_row(row):
    """Same as above from a Manifest.txt row; blank or '--' means 'absent'."""
    return {key.upper(): value for key, value in row.items()
            if key and value not in (None, '', '--')
            and key.lower() not in ('file', 'history')}


def night_of(path):
    """
    Return ``(night, night_dir)`` for the first ``YYYY-MM-DD`` component of
    the absolute path. Works whether the scan root is above the night
    directory or is the night directory itself. A path with no such
    component gets ``night=''`` and its own directory as ``night_dir``.
    """
    path = os.path.abspath(path)
    parts = path.split(os.sep)
    for i, part in enumerate(parts):
        if NIGHT_RE.match(part):
            return part, os.sep.join(parts[:i + 1])
    return '', os.path.dirname(path)


def classify(values):
    """Return ``(status, note)`` with status unpatched, partial, or ok."""
    if 'PURGED' not in values:
        # patch_headers dies before PURGED on files with no SWCREATE or no
        # IMAGETYP and does not list them in NEEDS_PATCHING.txt, so a re-run
        # cannot fix them.
        absent = [k for k in ('SWCREATE', 'IMAGETYP') if k not in values]
        note = f"no {','.join(absent)}; re-run will not fix" if absent else ''
        return 'unpatched', note
    missing = [k for k in ALWAYS_KEYS if k not in values]
    if missing:
        return 'unpatched', 'PURGED but missing ' + ','.join(missing)
    if values.get('IMAGETYP', '').strip().upper() == 'LIGHT':
        missing = [k for k in LIGHT_KEYS if k not in values]
        if missing:
            return 'partial', 'missing ' + ','.join(missing)
    return 'ok', ''


def make_record(path, source, values=None, error=None):
    night, night_dir = night_of(path)
    status, note = ('error', error) if error else classify(values)
    values = values or {}
    swcreate = values.get('SWCREATE', '')
    instrume = values.get('INSTRUME', '')
    return {
        'status': status, 'night': night, 'night_dir': night_dir,
        'file': path, 'source': source,
        'swcreate': swcreate, 'swcreate_known': swcreate in KNOWN_SWCREATE,
        'imagetyp': values.get('IMAGETYP', ''),
        'instrume': instrume, 'instrume_known': instrume in KNOWN_INSTRUME,
        'has_wcs': 'CTYPE1' in values, 'note': note,
    }


def records_from_manifest(dirpath):
    """Return ``(records, listed_file_names)`` or ``(None, set())``."""
    try:
        with open(os.path.join(dirpath, 'Manifest.txt'), newline='') as f:
            reader = csv.DictReader(f)
            # A manifest written without --all lacks the keywords we need.
            columns = {c.lower() for c in reader.fieldnames or []}
            if not {'file', 'purged'} <= columns:
                return None, set()
            # Rows for files deleted or renamed since triage ran are stale.
            rows = [row for row in reader if row.get('file')
                    and os.path.exists(os.path.join(dirpath, row['file']))]
    except (OSError, csv.Error):
        return None, set()
    records = [make_record(os.path.join(dirpath, row['file']), 'manifest',
                           values_from_row(row)) for row in rows]
    return records, {row['file'] for row in rows}


def record_from_header(path):
    try:
        values = values_from_header(fits.getheader(path))
    except Exception as e:
        return make_record(path, 'header', error=f'{type(e).__name__}: {e}')
    return make_record(path, 'header', values)


def scan(roots, since, use_manifest, quiet):
    """Yield one record per FITS file found under ``roots``."""
    n_headers = 0
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            night = night_of(dirpath)[0]
            if night:
                # run_patch.py/run_triage.py only touch the top level of a
                # night, so subdirectories (bad/, tracking/, ...) are not ours.
                dirnames[:] = []
                if since and night < since:
                    continue
            fits_names = sorted(n for n in filenames
                                if n.lower().endswith(FITS_EXTENSIONS))
            records, listed = None, set()
            if use_manifest and 'Manifest.txt' in filenames:
                records, listed = records_from_manifest(dirpath)
            yield from records or []
            # Everything the manifest did not cover is read from its header.
            for name in fits_names:
                if name in listed:
                    continue
                n_headers += 1
                if not quiet and n_headers % 500 == 0:
                    print(f'...read {n_headers} FITS headers', file=sys.stderr)
                yield record_from_header(os.path.join(dirpath, name))


def write_csv(records, output_path, include_ok):
    fields = ['status', 'night', 'file', 'source', 'swcreate', 'swcreate_known',
              'imagetyp', 'instrume', 'instrume_known', 'has_wcs', 'note']
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(r for r in records if include_ok or r['status'] != 'ok')


def print_summary(records):
    totals = Counter(r['status'] for r in records)
    print('Totals by status:')
    for status in ('ok', 'unpatched', 'partial', 'error'):
        print(f'  {status}: {totals[status]}')
    for source in ('manifest', 'header'):
        files = [r['file'] for r in records if r['source'] == source]
        dirs = {os.path.dirname(f) for f in files}
        print(f'  (from {source}: {len(files)} files in {len(dirs)} directories)')

    by_dir = defaultdict(list)
    for r in records:
        by_dir[r['night_dir']].append(r)

    print('\nDirectories with unpatched/partial/error files:')
    rerun_dirs = []
    for night_dir, recs in sorted(by_dir.items()):
        counts = Counter(r['status'] for r in recs)
        if not (counts['unpatched'] or counts['partial'] or counts['error']):
            continue
        unpatched = [r for r in recs if r['status'] == 'unpatched']
        unknown_sw = sorted({r['swcreate'] for r in unpatched if not r['swcreate_known']})
        unknown_inst = sorted({r['instrume'] for r in unpatched if not r['instrume_known']})
        print(f"  {night_dir}: n_unpatched={counts['unpatched']} "
              f"n_partial={counts['partial']} n_error={counts['error']} "
              f"n_total={len(recs)} "
              f"unknown_swcreate={','.join(unknown_sw) or '(none)'} "
              f"unknown_instrume={','.join(unknown_inst) or '(none)'}")
        if counts['unpatched'] or counts['error']:
            rerun_dirs.append(night_dir)
    if not any(r['status'] != 'ok' for r in records):
        print('  (none)')

    print('\nUnpatched files by SWCREATE:')
    sw_counts = Counter(r['swcreate'] for r in records if r['status'] == 'unpatched')
    for swcreate, count in sorted(sw_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        label = 'known' if swcreate in KNOWN_SWCREATE else 'UNKNOWN'
        print(f"  {count}  {swcreate or '(blank)'}  [{label}]")
    if not sw_counts:
        print('  (none)')

    # Nights with only 'partial' files are the NEEDS_POINTING_INFO cases
    # triage already reports, so they are not listed here.
    print('\nNight directories needing a re-run (unpatched or unreadable files):')
    for night_dir in rerun_dirs:
        print(night_dir)
    if not rerun_dirs:
        print('  (none)')


def main(argv=None):
    parser = argparse.ArgumentParser(description=(
        "Find FITS files that were never patched, or only partially patched, "
        "by msumastro's patch_headers."))
    parser.add_argument('roots', metavar='ROOT', nargs='*', default=DEFAULT_ROOTS,
                        help=f"Directories to scan (default: {' '.join(DEFAULT_ROOTS)})")
    parser.add_argument('--since', metavar='YYYY-MM-DD',
                        type=lambda s: datetime.strptime(s, '%Y-%m-%d').strftime('%Y-%m-%d'),
                        help='Skip nights before this date.')
    parser.add_argument('--output', metavar='PATH', default='unpatched_files.csv',
                        help='CSV output path (default: unpatched_files.csv)')
    parser.add_argument('--all', action='store_true',
                        help='Include "ok" rows in the CSV output too.')
    parser.add_argument('--no-manifest', action='store_true',
                        help='Ignore Manifest.txt and read every FITS header '
                             '(slow, but reflects the current state of the files).')
    parser.add_argument('--quiet', action='store_true',
                        help='Suppress progress messages on stderr.')
    args = parser.parse_args(argv)

    roots = []
    for root in args.roots:
        if os.path.isdir(root):
            roots.append(root)
        else:
            print(f'warning: root does not exist, skipping: {root}', file=sys.stderr)
    if not roots:
        print('error: none of the given roots exist', file=sys.stderr)
        return 1

    records = list(scan(roots, args.since, not args.no_manifest, args.quiet))
    write_csv(records, args.output, args.all)
    print_summary(records)
    return int(any(r['status'] in ('unpatched', 'error') for r in records))


if __name__ == '__main__':
    sys.exit(main())
