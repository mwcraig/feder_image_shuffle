import os
from argparse import ArgumentParser
import logging

from astropy.table import Table
from ccdproc import ImageFileCollection
from msumastro.header_processing.fitskeyword import FITSKeyword

logger = logging.getLogger()
logger.setLevel(logging.INFO)
console = logging.StreamHandler()
fil = logging.FileHandler('adding_observer.log')
logger.addHandler(console)
logger.addHandler(fil)


def obs_date(str):
    """
    Extract date of the form YYYY-MM-DD from a string

    Parameters
    ----------

    str : str
        A string which contains a date.

    Returns
    -------

    str
        The date, as a string
    """
    import re
    get_date = re.compile(r'.*\/(\d{4,4}-\d\d-\d\d).*')
    match = get_date.search(str)
    date = match
    if date:
        date = match.group(1)
    return date


def add_observer(top_of_tree, observers):
    """
    Add observer name to each of the FITS files in a tree of directories

    Parameters
    ----------

    top_of_tree : str
        Path to top of the directory tree containing the images to be modified
    observers : dict
        Dictionary with observation date of the form YYYY-MM-DD as keys and
        name(s) of observer(s) as a single string as the value.

    .. warning::
        This function will overwrite the FITS files in the tree.
    """
    for root, dirs, files in os.walk(top_of_tree):
        date = obs_date(root)
        if not date:
            continue
        logging.info('Processing directory %s with observers: %s',
                     root, observers[date])
        ic = ImageFileCollection(root, keywords=['imagetyp'])
        observer_keyword = FITSKeyword(name='observer', value=observers[date])
        for hdr, fname in ic.headers(clobber=True, return_fname=True):
            if ('observer' in hdr) and hdr['purged']:
                logging.warning('Skipping file %s in %s because observer '
                                'has already been added', fname, root)
                continue
            observer_keyword.add_to_header(hdr, history=True)


def construct_observer_dict(observer_file):
    """
    Turn list of observers into a dictionary

    Parameters
    ----------

    observer_file : str
        Name of file with two columns: night and observer, in an ASCII
        format understandable by astropy.table. Multiple observers should all
        be listed in one column.
    """
    table = Table.read(observer_file, format='ascii')
    observers = {}
    for date, names in table:
        observers[date] = names
    return observers


def construct_parser():
    #short_desc = 'Little script to add observer names to FITS files'
    parser = ArgumentParser()
    parser.add_argument('top_of_tree',
                        help='Path to top of directory tree containing images')
    parser.add_argument('observer_list',
                        help='Name of file containing observers/nights')
    return parser


def main(arglist=None):
    parser = construct_parser()
    args = parser.parse_args(arglist)
    observers = construct_observer_dict(args.observer_list)
    add_observer(args.top_of_tree, observers)

if __name__ == '__main__':
    main()
