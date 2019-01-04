#!/bin/bash

# THIS FILE IS OUT OF BOUNDS
# and bugs in this file aren't in bounds either

set -e  # die on failure

git log -n 4
echo
echo commit: "$TRAVIS_PULL_REQUEST_SHA"

if [ -z "$TRAVIS_REPO_SLUG" ]; then
  echo "Missing repo."
  exit 1
fi

if [ -z "$TRAVIS_PULL_REQUEST" ]; then
  echo "Missing PR number."
  exit 1
fi

if [ "$TRAVIS_PULL_REQUEST" = "false" ]; then
  if [ "$(git rev-parse --abbrev-ref HEAD)" != "master" ]; then
    echo "Branch builds on pull requests are ignored"
    exit 0
  fi
fi

if [ -d tmp-nomic-master ]; then
  rm -rf tmp-nomic-master
fi

git clone --depth=1 https://github.com/${TRAVIS_REPO_SLUG}.git tmp-nomic-master

cd tmp-nomic-master

python3 validate.py

cd ..

rm -rf tmp-nomic-master
