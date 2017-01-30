# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) The Spyder Development Team
#
# Licensed under the terms of the MIT License
# (See LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Loghub filter and formatter."""

# yapf: disable

# Standard library imports
from collections import OrderedDict
import re
import time

# Third party imports
from jinja2 import Template

# Local imports
from loghub.core.repo import GitHubRepo
from loghub.templates import (CHANGELOG_GROUPS_TEMPLATE_PATH,
                              CHANGELOG_TEMPLATE_PATH,
                              RELEASE_GROUPS_TEMPLATE_PATH,
                              RELEASE_TEMPLATE_PATH)


# yapf: enable


def filter_prs_by_regex(issues, pr_label_regex):
    """Filter prs by issue regex."""
    filtered_prs = []
    pr_pattern = re.compile(pr_label_regex)

    for issue in issues:
        is_pr = bool(issue.get('pull_request'))
        labels = ' '.join(issue.get('loghub_label_names'))

        if is_pr and pr_label_regex:
            pr_valid = bool(pr_pattern.search(labels))
            if pr_valid:
                filtered_prs.append(issue)
        if is_pr and not pr_label_regex:
            filtered_prs.append(issue)

    return filtered_prs


def filter_issues_by_regex(issues, issue_label_regex):
    """Filter issues by issue regex."""
    filtered_issues = []
    issue_pattern = re.compile(issue_label_regex)

    for issue in issues:
        is_pr = bool(issue.get('pull_request'))
        is_issue = not is_pr
        labels = ' '.join(issue.get('loghub_label_names'))

        if is_issue and issue_label_regex:
            issue_valid = bool(issue_pattern.search(labels))
            if issue_valid:
                filtered_issues.append(issue)
        elif is_issue and not issue_label_regex:
            filtered_issues.append(issue)

    return filtered_issues


def filter_issue_label_groups(issues, issue_label_groups):
    """Filter issues by the label groups."""
    grouped_filtered_issues = OrderedDict()
    if issue_label_groups:
        new_filtered_issues = []
        for label_group_dic in issue_label_groups:
            grouped_filtered_issues[label_group_dic['name']] = []

        for issue in issues:
            for label_group_dic in issue_label_groups:
                labels = issue.get('loghub_label_names')
                label = label_group_dic['label']
                name = label_group_dic['name']
                if label in labels:
                    grouped_filtered_issues[name].append(issue)
                    new_filtered_issues.append(issue)

        # Remove any empty groups
        for group, grouped_issues in grouped_filtered_issues.copy().items():
            if not grouped_issues:
                grouped_filtered_issues.pop(group)
    else:
        new_filtered_issues = issues

    return new_filtered_issues, grouped_filtered_issues


def create_changelog(repo=None,
                     username=None,
                     password=None,
                     token=None,
                     milestone=None,
                     since_tag=None,
                     until_tag=None,
                     branch=None,
                     output_format='changelog',
                     issue_label_regex='',
                     pr_label_regex='',
                     template_file=None,
                     issue_label_groups=None):
    """Create changelog data."""
    # Instantiate Github API
    gh = GitHubRepo(
        username=username,
        password=password,
        token=token,
        repo=repo, )

    version = until_tag or None
    milestone_number = None
    closed_at = None
    since = None
    until = None
    version_tag_prefix = 'v'

    # Set milestone or from tag
    if milestone and not since_tag:
        milestone_data = gh.milestone(milestone)
        milestone_number = milestone_data['number']
        closed_at = milestone_data['closed_at']
        version = milestone

        if version.startswith(version_tag_prefix):
            version = version[len(version_tag_prefix):]

    elif not milestone and since_tag:
        since = gh.tag(since_tag)['tagger']['date']
        if until_tag:
            until = gh.tag(until_tag)['tagger']['date']
            closed_at = until

    # This returns issues and pull requests
    issues = gh.issues(
        milestone=milestone_number,
        state='closed',
        since=since,
        until=until,
        branch=branch, )

    # Filter by regex if available
    filtered_prs = filter_prs_by_regex(issues, pr_label_regex)
    filtered_issues = filter_issues_by_regex(issues, issue_label_regex)

    # If issue label grouping, filter issues
    new_filtered_issues, issue_label_groups = filter_issue_label_groups(
        filtered_issues, issue_label_groups)

    return format_changelog(
        repo,
        new_filtered_issues,
        filtered_prs,
        version,
        closed_at=closed_at,
        output_format=output_format,
        template_file=template_file,
        issue_label_groups=issue_label_groups)


def format_changelog(repo,
                     issues,
                     prs,
                     version,
                     closed_at=None,
                     output_format='changelog',
                     output_file='CHANGELOG.temp',
                     template_file=None,
                     issue_label_groups=None):
    """Create changelog data."""
    # Header
    if not version:
        version = '<RELEASE_VERSION>'

    if closed_at:
        close_date = closed_at.split('T')[0]
    else:
        close_date = time.strftime("%Y/%m/%d")

    # Load template
    if template_file:
        filepath = template_file
    else:
        if issue_label_groups:
            if output_format == 'changelog':
                filepath = CHANGELOG_GROUPS_TEMPLATE_PATH
            else:
                filepath = RELEASE_GROUPS_TEMPLATE_PATH
        else:
            if output_format == 'changelog':
                filepath = CHANGELOG_TEMPLATE_PATH
            else:
                filepath = RELEASE_TEMPLATE_PATH

    with open(filepath) as f:
        data = f.read()

    repo_owner, repo_name = repo.split('/')
    template = Template(data)
    rendered = template.render(
        issues=issues,
        pull_requests=prs,
        version=version,
        close_date=close_date,
        repo_full_name=repo,
        repo_owner=repo_owner,
        repo_name=repo_name,
        issue_label_groups=issue_label_groups, )

    print('#' * 79)
    print(rendered)
    print('#' * 79)

    with open(output_file, 'w') as f:
        f.write(rendered)

    return rendered
