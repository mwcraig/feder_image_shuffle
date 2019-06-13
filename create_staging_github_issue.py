from __future__ import print_function, absolute_import, unicode_literals

import os
from glob import glob
from time import sleep

from github3 import login

LABELS = {
    'NEEDS_ASTROMETRY.txt': 'needs astrometry',
    'NEEDS_POINTING_INFO.txt': 'needs pointing',
    'NEEDS_OBJECT_NAME.txt': 'needs object'
}

ISSUE_NAME_BASE = 'Examine staged data for {night}'


def add_needs_contents_to_issue(issue, needs_path):
    """
    Add the contents of each file in needs_path to the issue as a
    comment.
    """
    for path in needs_path:
        with open(path, 'r') as f:
            contents = f.read()
        need = os.path.basename(path)
        comment_body = '## {}\n```{}```'.format(need, contents)
        issue.create_comment(comment_body)


def get_github_repo():
    token = os.getenv('GITHUB_TOKEN')

    if not token:
        raise RuntimeError('Set GITHUB_TOKEN to a github token before running.')
    gh = login(token=token)

    return gh.repository('feder-observatory', 'processed_images')


def get_needs_from_disk(path):
    if path is not None:
        needs_stuff_paths = glob(os.path.join(path, 'NEEDS*.txt'))
        # Do not write full path to github.
        needs_stuff = [os.path.basename(need) for need in needs_stuff_paths]
    else:
        needs_stuff = []
    return needs_stuff


def main(night, path=None, sleep_time=0.1, gallery=None):
    """
    Create a github issue for a night that has been staged.

    Parameters
    ----------

    night : str
        Date of the observation, in the form YYYY-MM-DD

    path : str
        Full path the the directory containing the staged images.

    sleep_time : float
        Amount of time to sleep after the github class to avoid hitting API
        rate limits.
    """
    if gallery is None:
        gallery = ''

    repo = get_github_repo()

    # Check whether there is already an issue for this night.
    issue_title = ISSUE_NAME_BASE.format(night=night)
    for i in repo.issues():
        if i.title == issue_title:
            raise RuntimeError('Issue already exists: {}'.format(issue_title))

    # Add a skeleton README for this night
    with open('github_staging_readme_template.md', 'r') as f:
        template = f.read()

    readme = template.format(night=night, image_gallery=gallery)
    readme_path = 'nights/{}-README.md'.format(night)
    commit_message = 'Add skeleton README for {}'.format(night)
    repo.create_file(readme_path, commit_message, readme.encode('utf-8'))

    readme_edit_url = '/'.join([repo.html_url, 'edit', 'master', readme_path])

    needs_stuff = get_needs_from_disk(path)

    if needs_stuff:
        needs_text = ('\n\nThis directory seems to need '
                      'these things:\n+ {}').format('\n+ '.join(needs_stuff))
    else:
        needs_text = ''

    if gallery:
        gallery_text = '\nRaw images for this night at: {}\n'.format(gallery)
    else:
        gallery_text = ''

    issue_text = (('Click [here]({}) to edit README '
                  'for this night'.format(readme_edit_url)) +
                  gallery_text + needs_text)

    issue = repo.create_issue(issue_title, issue_text)

    # Add labels if we need them
    labels = [label for key, label in LABELS.items()
              if key in needs_stuff]

    if labels:
        issue.add_labels(*labels)

    needs_stuff_paths = [os.path.join(path, need) for need in needs_stuff]
    add_needs_contents_to_issue(issue, needs_stuff_paths)

    # Take a brief nap to avoid getting blocked by GitHub...
    sleep(sleep_time)


def add_arguments(parser, include_gallery_option=True):
    parser.add_argument('night', help='Night of observation as YYYY-MM-DD')
    parser.add_argument('-p', '--path',
                        help='Full path to directory containing observations',
                        nargs=1, default=None)
    if include_gallery_option:
        parser.add_argument('-g', '--gallery',
                            help='URL for image gallery',
                            nargs=1, default=None)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    add_arguments(parser)
    args = parser.parse_args()

    # If provided, path and gallery will be returned as a list, so get the
    # value from the list if user has provided a value.
    path = args.path
    gallery = args.gallery
    if path:
        path = path[0]
    if gallery:
        gallery = gallery[0]

    main(args.night, path=path, gallery=gallery)
