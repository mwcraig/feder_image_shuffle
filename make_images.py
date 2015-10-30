from __future__ import (division, print_function,
                        unicode_literals, absolute_import)

import os
import argparse

import numpy as np

from skimage.measure import block_reduce

from astropy.visualization import scale_image

import matplotlib.image as mimg

from msumastro import ImageFileCollection


def scale_and_downsample(data, downsample=4,
                         min_percent=20,
                         max_percent=99.5):

    scaled_data = scale_image(data,
                              min_percent=min_percent,
                              max_percent=max_percent)

    if downsample > 1:
        scaled_data = block_reduce(scaled_data,
                                   block_size=(downsample, downsample))
    return scaled_data


def main(source_d, destination_d, thumbnail_size=150):
    """
    Create a directory of jpegs from a directory of FITS files, optionally
    creating a subdirectory of jpeg thumbnails.

    Parameters
    ----------

    source_d : str
        Path to the directory of FITS files.

    destination_d : str
        Path to the directory in which JPEGs will be placed.

    thumbnail_size: float
        Dimension of thumbnail image. Set to zero to not produce thumbnails.
    """
    thumbnail_dir = 'thumbnail'

    ic = ImageFileCollection(source_d, keywords='*')

    os.makedirs(destination_d)
    if thumbnail_size:
        os.makedirs(os.path.join(destination_d, thumbnail_dir))

    for data, fname in ic.data(return_fname=True):
        scaled_data = scale_and_downsample(data)
        base, _ = os.path.splitext(os.path.basename(fname))
        dest_path = os.path.join(destination_d, base + '.jpg')
        mimg.imsave(dest_path, scaled_data, cmap="gray")

        if thumbnail_size:
            tiny = np.array(data.shape) // thumbnail_size
            thumb = block_reduce(scaled_data, block_size=tuple(tiny))
            thumb_path = os.path.join(destination_d, thumbnail_dir, base + '.jpg')
            mimg.imsave(thumb_path, thumb, cmap='gray')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make JPG images of FITS files')
    parser.add_argument('source_directory')
    parser.add_argument('destination_directory')

    args = parser.parse_args()
    main(args.source_directory, args.destination_directory)
