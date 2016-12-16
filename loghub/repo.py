# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) The Spyder Development Team
#
# Licensed under the terms of the MIT License
# (See LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Github repo wrapper."""

from __future__ import print_function

# Standard library imports
import datetime
import sys

# Local imports
from loghub.external.github import GitHub, ApiError, ApiNotFoundError


class GitHubRepo(object):
    """Github repository wrapper."""

    def __init__(self, username=None, password=None, token=None, repo=None):
        """Github repository wrapper."""
        self._username = username
        self._password = password
        self._repo = repo
        self.gh = GitHub(
            username=username,
            password=password,
            access_token=token, )
        repo_organization, repo_name = repo.split('/')
        self.repo = self.gh.repos(repo_organization)(repo_name)

        # Check organization/username
        try:
            self.gh.users(repo_organization).get()
        except ApiNotFoundError as error:
            print('LOGHUB: Organization/user `{}` seems to be '
                  'invalid.\n'.format(repo_organization))
            sys.exit(1)
        except ApiError as error:
            self._check_rate()

        # Check repo
        try:
            self.repo.get()
        except ApiNotFoundError as error:
            print('LOGHUB: Repository `{0}` for organization/username `{1}` '
                  'seems to be invalid.\n'.format(repo_name,
                                                  repo_organization))
            sys.exit(1)
        except ApiError as error:
            self._check_rate()

        sys.exit(1)

    def _check_rate(self):
        """Check and handle if api rate limit has been exceeded."""
        if self.gh.x_ratelimit_remaining == 0:
            print('LOGHUB: GitHub API rate limit exceeded!\n')
            if not self._username and not self._password or not self._token:
                print('LOGHUB: Try running loghub with user/password or '
                      'token.\n')
            sys.exit(1)

    def tags(self):
        """Return all tags."""
        self._check_rate()
        return self.repo('git')('refs')('tags').get()

    def tag(self, tag_name):
        """Get tag information."""
        self._check_rate()
        refs = self.repo('git')('refs')('tags').get()
        sha = -1
        for ref in refs:
            ref_name = 'refs/tags/{tag}'.format(tag=tag_name)
            if 'object' in ref and ref['ref'] == ref_name:
                sha = ref['object']['sha']
                break

        if sha == -1:
            print("You didn't pass a valid tag name!")
            sys.exit(1)

        return self.repo('git')('tags')(sha).get()

    def milestones(self):
        """Return all milestones."""
        self._check_rate()
        return self.repo.milestones.get(state='all')

    def milestone(self, milestone_title):
        """Return milestone with given title."""
        self._check_rate()
        milestones = self.milestones()
        milestone_number = -1
        for milestone in milestones:
            if milestone['title'] == milestone_title:
                milestone_number = milestone['number']
                break

        if milestone_number == -1:
            print("You didn't pass a valid milestone name!")
            sys.exit(1)

        return milestone

    def pr(self, pr_number):
        """Get PR information."""
        self._check_rate()
        return self.repo('pulls')(str(pr_number)).get()

    def issues(self,
               milestone=None,
               state=None,
               assignee=None,
               creator=None,
               mentioned=None,
               labels=None,
               sort=None,
               direction=None,
               since=None,
               until=None,
               branch=None):
        """Return Issues and Pull Requests."""
        self._check_rate()
        page = 1
        issues = []
        while True:
            result = self.repo.issues.get(page=page,
                                          per_page=100,
                                          milestone=milestone,
                                          state=state,
                                          assignee=assignee,
                                          creator=creator,
                                          mentioned=mentioned,
                                          labels=labels,
                                          sort=sort,
                                          direction=direction,
                                          since=since)
            if len(result) > 0:
                issues += result
                page = page + 1
            else:
                break

        # If since was provided, filter the issue
        if since:
            since_date = self.str_to_date(since)
            for issue in issues[:]:
                close_date = self.str_to_date(issue['closed_at'])
                if close_date < since_date and issue in issues:
                    issues.remove(issue)

        # If until was provided, filter the issue
        if until:
            until_date = self.str_to_date(until)
            for issue in issues[:]:
                close_date = self.str_to_date(issue['closed_at'])
                if close_date > until_date and issue in issues:
                    issues.remove(issue)

        # If it is a pr check if it is merged or closed, removed closed ones
        for issue in issues[:]:
            pr = issue.get('pull_request', '')

            # Add label names inside additional key
            issue['loghub_label_names'] = [
                l['name'] for l in issue.get('labels')
            ]

            if pr:
                number = issue['number']
                if not self.is_merged(number) and issue in issues:
                    issues.remove(issue)

                if branch:
                    # Get PR info and get base branch
                    pr_data = self.pr(number)
                    base_ref = pr_data['base']['ref']
                    if base_ref != branch and issue in issues:
                        issues.remove(issue)

        return issues

    def is_merged(self, pr):
        """
        Return wether a PR was merged, or if it was closed and discarded.

        https://developer.github.com/v3/pulls/#get-if-a-pull-request-has-been-merged
        """
        self._check_rate()
        merged = True
        try:
            self.repo('pulls')(str(pr))('merge').get()
        except Exception:
            merged = False
        return merged

    @staticmethod
    def str_to_date(string):
        """Convert ISO date string to datetime object."""
        parts = string.split('T')
        date_parts = parts[0]
        time_parts = parts[1][:-1]
        year, month, day = [int(i) for i in date_parts.split('-')]
        hour, minutes, seconds = [int(i) for i in time_parts.split(':')]
        return datetime.datetime(year, month, day, hour, minutes, seconds)
