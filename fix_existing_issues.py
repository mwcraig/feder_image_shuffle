from __future__ import print_function, absolute_import, unicode_literals

import os
from time import sleep
import argparse
import subprocess
import shutil

from github3 import login

from create_staging_github_issue import add_needs_contents_to_issue, LABELS
import make_images
import make_viewer_pages

BASE_GALLERY_URL = 'http://physics.mnstate.edu/feder_gallery/'


def night_from_issue(issue):
    """
    Return the night corresponding to issue.

    Parameters
    ----------

    issue: github3 Issue object
        Issue corresponding to a night of data.

    Returns
    -------

    str
        Night corresponding to the issue.
    """
    name = issue.title
    # Night should be last 10 digits, in form YYYY-MM-DD
    night = name[-10:]
    return night


def fix_needs_contents(issue, night_path, need_label):
    for fname, label in LABELS.iteritems():
        if label == need_label:
            need_file_name = fname
            break
    else:
        raise RuntimeError('No label matching {}'.format(need_label))

    needs_stuff_path = os.path.join(night_path, need_file_name)
    add_needs_contents_to_issue(issue, [needs_stuff_path])


def fix_gallery(issue, staged_images_path, jpeg_base_path,
                server_destination, base_url=BASE_GALLERY_URL):
    night = night_from_issue(issue)
    jpeg_path = os.path.join(jpeg_base_path, night)
    print('Making images for {}'.format(night))
    make_images.main(staged_images_path, jpeg_path)
    print('Making viewer page for {}'.format(night))
    night_url = base_url + '/' + night
    viewer_page = make_viewer_pages.main(staged_images_path, jpeg_path,
                                         night_url, night)
    with open(os.path.join(jpeg_path, 'index.html'), 'w') as f:
        f.write(str(viewer_page))
    shutil.copy('magnific-popup.css', jpeg_path)
    shutil.copy('jquery.magnific-popup.js', jpeg_path)
    print('Pushing jpeg and viewer page to server...')
    subprocess.check_call(['rsync', '-e', 'ssh', '-av', jpeg_path,
                           server_destination])
    # Edit the body of the issue to include a link to the gallery
    print('Adding gallery to the body of the issue...')
    body = issue.body
    body = '\n\n'.join([body, 'Image gallery for this night at: ', night_url])
    issue.edit(body=body)


def main(label, fix, base_path_to_staged_images,
         gallery_destination=None, jpeg_destination=None):

    token = os.getenv('GITHUB_TOKEN')

    if not token:
        raise RuntimeError('Set GITHUB_TOKEN to a github token '
                           'before running.')

    gh = login(token=token)
    repo = gh.repository('feder-observatory', 'processed_images')

    for issue in repo.issues(state='open', labels=label):
        night_path = os.path.join(base_path_to_staged_images,
                                  night_from_issue(issue))
        for l in issue.labels():
            if l.name in [foo for foo in LABELS.values()]:
                if fix == 'needs':
                    fix_needs_contents(issue, night_path, l.name)
                elif fix == 'gallery':
                    fix_gallery(issue, night_path,
                                jpeg_destination, gallery_destination)
        # Success, so remove the label.
        issue.remove_label(label)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Fix up existing github issues that are '
                                     'missing the latest and greatest '
                                     'features')

    parser.add_argument('fix', choices=['needs', 'gallery'],
                        help='Action to take for each issue')

    parser.add_argument('--label', action='store', default='',
                        help='Label of issue(s) to which fix will be applied.'
                        ' Omit to apply fix to all open issues.')

    parser.add_argument('-b', '--base-path', default='.',
                        help='Base path to images such that the base path '
                        'plus night name is the path to the staged images for '
                        'the night corresponding to the issue to be fixed.')

    parser.add_argument('--server-uri',
                        default='matt.craig@physics:/data/feder/gallery',
                        help='Destination for jpeg images; will be passed '
                             'in to rsync')

    parser.add_argument('-j', '--jpeg-dir-base', default='.',
                        help='Directory holding the jpeg images.')

    args = parser.parse_args()

    main(args.label, args.fix, args.base_path,
         gallery_destination=args.server_uri,
         jpeg_destination=args.jpeg_dir_base)
