from __future__ import print_function, absolute_import, unicode_literals

import os
from github3 import login


def main(night):
    token = os.getenv('GITHUB_TOKEN')

    if not token:
        raise RuntimeError('Set GITHUB_TOKEN to a github token before running.')

    gh = login(token=token)
    repo = gh.repository('feder-observatory', 'processed_images')

    # Add a skeleton README for this night
    with open('github_staging_readme_template.md', 'r') as f:
        template = f.read()

    readme = template.format(night=night)
    readme_path = 'nights/{}-README.md'.format(night)
    commit_message = 'Add skeleton README for {}'.format(night)
    repo.create_file(readme_path, commit_message, readme)

    readme_edit_url = '/'.join([repo.html_url, 'edit', 'master', readme_path])
    issue = repo.create_issue('Examine staged data for {}'.format(night),
                              'Click [here]({}) to edit README for this night'.format(readme_edit_url))

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('night', help='Night of observation as YYYY-MM-DD')

    args = parser.parse_args()

    main(args.night)
