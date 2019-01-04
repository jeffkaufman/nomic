#!/bin/bash

# THIS FILE IS OUT OF BOUNDS
# and bugs in this file aren't in bounds either

set -e  # die on failure

if [ -z "$TRAVIS_REPO_SLUG" ]; then
  echo "Missing repo."
  exit 1
fi

if [ -z "$TRAVIS_PULL_REQUEST" ]; then
  echo "Missing PR number."
  exit 1
fi

if [ "$TRAVIS_PULL_REQUEST" = "false" ]; then
  BRANCH=$(git rev-parse --abbrev-ref HEAD)
  echo "On branch $BRANCH"
  if [ "$BRANCH" != "master" ]; then
    echo "Branch builds on pull requests are ignored"
    exit 0
  fi
fi

if [ -d tmp-nomic-master ]; then
  rm -rf tmp-nomic-master
fi

git clone --depth=1 https://github.com/${TRAVIS_REPO_SLUG}.git tmp-nomic-master

cd tmp-nomic-master

python3 validate.py  # first validate by the master rules

cd ..

rm -rf tmp-nomic-master

python3 validate.py  # now validate by the new proposed rules
