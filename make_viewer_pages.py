from __future__ import division, print_function, absolute_import

from collections import OrderedDict
import os
import argparse

import jinja2
from msumastro import ImageFileCollection


def construct_image_title(filename, header):
    title = ''

    if header['imagetyp'] == 'LIGHT' or header['imagetyp'] == 'FLAT':
        title = '   '.join([title, 'Filter:', header.get('filter', 'UNKNOWN')])

    title = ' '.join([title, 'Exposure: ', str(header['exposure'])])

    return title


def main(fits_directory, jpeg_directory, base_url, night,
         thumbnail_directory='thumbnail',
         org_by=None):
    """

    org_by: list, optional
        List of FITS keywords by which the files should be organized.
    """

    ic = ImageFileCollection(fits_directory, keywords='*')

    groups = ['BIAS', 'DARK', 'FLAT', 'LIGHT']

    image_groups = OrderedDict()
    for group in groups:
        images = []
        for header, fname in ic.headers(imagetyp=group, return_fname=True):
            f = os.path.basename(fname)
            images.append({'jpeg_name': f.replace('.fit', '.jpg'),
                           'title': construct_image_title(f, header),
                           'original_name': f})
        image_groups[group] = images

    loader = jinja2.FileSystemLoader('.')
    e = jinja2.Environment(loader=loader, autoescape=True)

    template = e.get_template('viewer_page.html')

    foo = template.render(night=night, base_url=base_url,
                          image_groups=image_groups,
                          base_url_thumb=os.path.join(base_url,
                                                      thumbnail_directory))

    return foo


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Make a web page for viewing images')
    parser.add_argument('fits_directory',
                        help='Directory containing FITS images used to '
                             'generate the jpegs.')
    parser.add_argument('-j', '--jpeg_dir', default='.',
                        help='Directory holding the jpeg images.')
    parser.add_argument('-b', '--base-url', default='.',
                        help='URL to the folder holding the jpegs. The '
                             'default works if the images and the web page'
                             'are in the same folder.')
    parser.add_argument('-n', '--night', default='',
                        help='Night to use as page title. Default is to use'
                             'the last part of the fits_directory.')
    args = parser.parse_args()

    if args.night:
        night = args.night
    else:
        if args.fits_directory.endswith('/'):
            night = args.fits_directory[:-1]
        else:
            night = args.fits_directory

        _, night = os.path.split(night)

    print(main(args.fits_directory, args.jpeg_dir, args.base_url, night))
