# loghub

## Build status
[![Code Issues](https://www.quantifiedcode.com/api/v1/project/b5e47eec1e564a66a8c52c989880637b/badge.svg)](https://www.quantifiedcode.com/app/project/b5e47eec1e564a66a8c52c989880637b)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/spyder-ide/loghub/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/spyder-ide/loghub/?branch=master)

## Description
Changelog generator based on milestone or tags for github.

## Installation

Using pip

`pip install loghub`

Using conda

`conda install loghub -c conda-forge

## Usage

```bash
usage: loghub [-h] [-m MILESTONE] [-st SINCE_TAG] [-ut UNTIL_TAG]
              [-f OUTPUT_FORMAT] [-u USER] [-p PASSWORD]
              repository

Script to print the list of issues and pull requests closed in a given
milestone

positional arguments:
  repository            Repository name to generate the Changelog for, in the
                        form user/repo or org/repo (e.g. spyder-ide/spyder)

optional arguments:
  -h, --help            show this help message and exit
  -m MILESTONE, --milestone MILESTONE
                        Github milestone to get issues and pull requests for
  -st SINCE_TAG, --since-tag SINCE_TAG
                        Github issues and pull requests since tag
  -ut UNTIL_TAG, --until-tag UNTIL_TAG
                        Github issues and pull requests until tag
  -f OUTPUT_FORMAT, --format OUTPUT_FORMAT
                        Format for print, either 'changelog' (for Changelog.md
                        file) or 'release' (for the Github Releases page).
                        Default is 'changelog'. The 'release' option doesn't
                        generate Markdown hyperlinks.
  -u USER, --user USER  Github user name
  -p PASSWORD, --password PASSWORD
                        Github user password
```
