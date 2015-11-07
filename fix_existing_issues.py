from __future__ import print_function, absolute_import, unicode_literals

import os
from glob import glob
from time import sleep
import argparse

from github3 import login

from create_staging_github_issue import add_needs_contents_to_issue, LABELS


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


def main(label, fix, base_path_to_staged_images):
    fixes = {'needs': fix_needs_contents,
             'gallery': None}

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
                fixes[fix](issue, night_path, l.name)


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

    args = parser.parse_args()

    main(args.label, args.fix, args.base_path)
