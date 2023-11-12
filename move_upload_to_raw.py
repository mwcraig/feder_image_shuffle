from argparse import ArgumentParser
from filecmp import dircmp
from pathlib import Path
import shutil


def main():
    """
    Move every directory that is in upload and processed but not
    in raw to the folder raw.

    This is part of the normal workflow but for some reason is not currently
    part of stage_to_processed.
    """
    upload = Path('/data/feder/data/upload')
    up_nights = sorted(upload.glob('????-??-??'))

    processed = Path('/data/feder/data/processed')
    proc_globs = processed.glob('????-??-??')
    proc_nights = [p.stem for p in proc_globs]

    raw = Path('/data2/feder/data/raw')
    raw_nights = [p.stem for p in raw.glob('????-??-??')]

    for night in up_nights[:1]:

        if (night.stem in proc_nights) and (night not in raw_nights):
            print(f"Moving night {night}")
            destination = shutil.copytree(night, raw / night.stem)
            dcmp = dircmp(night, destination)
            if len(dcmp.diff_files) == 0:
                # Success, delete the old night
                shutil.rmtree(night)
                print(f"👍👍👍👍 {night}")
            else:
                raise RuntimeError(f'Error copying folder {night} to {destination}')

        else:
            print(f'--> Not moving {night}')


if __name__ == '__main__':
    # No arguments, but add a description at least
    parser = ArgumentParser(description=main.__doc__, add_help=True)
    args = parser.parse_args()
    main()
