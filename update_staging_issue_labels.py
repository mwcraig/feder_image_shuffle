import os
from glob import glob
from time import sleep

from github3 import login

from create_staging_github_issue import (LABELS, ISSUE_NAME_BASE,
                                         get_github_repo, add_arguments,
                                         get_needs_from_disk,
                                         add_needs_contents_to_issue)


def update_issue(repo, night=None, path=None, sleep_time=0.1):
    """
    Update (if necessary) the labels attached to the issue for this night
    on github.
    """

    # Grab all of the issues and issue numbers as a dict
    #issues = repo.issues()
    #print(dir(next(issues)))
    repo_issues = {issue.title: issue for issue in repo.issues()
                   if not issue.is_closed()}

    issue_name = ISSUE_NAME_BASE.format(night=night)

    issue = repo_issues[issue_name]
    if issue_name not in repo_issues.keys():
        raise RuntimeError("No open issue for night {}".format(night))

    needs = get_needs_from_disk(path)

    # Get the label names for the stuff we need.
    labels = [label for key, label in LABELS.items()
              if key in needs]

    if set(labels) == set(label.name for label in issue.labels()):
        # Nothing to do, so return
        print('Nothing to do for night {}'.format(night))
        return

    # Remove any needs labels present on this issue...
    for label in LABELS.values():
        issue.remove_label(label)

    # ...then add labels for the current needs...
    if labels:
        issue.add_labels(*labels)

    # ...and, finally, add new comments detailing those needs.
    needs_stuff_paths = [os.path.join(path, need) for need in needs]
    add_needs_contents_to_issue(issue, needs_stuff_paths)

    # Take a brief nap to avoid getting blocked by GitHub...
    sleep(sleep_time)


if __name__ == '__main__':
    import argparse

    repo = get_github_repo()

    parser = argparse.ArgumentParser()
    add_arguments(parser, include_gallery_option=False)
    args = parser.parse_args()

    path = args.path
    night = args.night
    if path:
        path = path[0]
        path_to_night = os.path.join(path, night)

    update_issue(repo, night=args.night, path=path_to_night)
