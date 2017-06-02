from __future__ import print_function

from argparse import ArgumentParser
import os

from ccdproc import ImageFileCollection

# Open files with io.fits instead of handling through ccdproc because it has
# not had a release since this issue was fixed.

from astropy.io import fits


def fix_headers(folder):
    """
    Find FITS files in folder that have WCS CTYPE ``RA--TAN`` and ``DEC--TAN``
    and add ``-SIP`` to the end. Necessary because astropy handling of SIP
    distortion keywords changed in v1.2.

    Parameters
    ----------

    folder : str
        Path to folder with the images to fix.
    """
    ic = ImageFileCollection(folder)
    ic.summary['ctype1']

    files = ic.files_filtered(ctype1='RA---TAN')

    if not files:
        print('No files to fix in {}'.format(folder))

    for file in files:
        fname = os.path.join(folder, file)
        print('Fixing file {}'.format(file))
        with fits.open(fname) as f:
            f[0].header['ctype1'] = f[0].header['ctype1'] + '-SIP'
            f[0].header['ctype2'] = f[0].header['ctype2'] + '-SIP'
            f.writeto(fname, clobber=True)


def main(args=None):
    if args is None:
        parser = ArgumentParser(description='Really hacky fix to WCS '
                                'SIP keywords')
        parser.add_argument('directory', help='Folder to modify IN PLACE. As '
                            'in your files WILL BE OVERWRITTEN.')

        args = parser.parse_args()

    fix_headers(args.directory)


if __name__ == '__main__':
    main()
