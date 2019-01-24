#!/bin/bash

# THIS FILE IS OUT OF BOUNDS
# and bugs in this file aren't in bounds either

set -e  # die on failure

echo 'Testing that build failures send notifications'
exit 1

if [ -z "$TRAVIS_REPO_SLUG" ]; then
  echo "Missing repo."
  exit 1
fi

if [ -z "$TRAVIS_PULL_REQUEST" ]; then
  echo "Missing PR number."
  exit 1
fi

if [ -d tmp-nomic-master ]; then
  rm -rf tmp-nomic-master
fi

git clone https://github.com/${TRAVIS_REPO_SLUG}.git tmp-nomic-master

cd tmp-nomic-master

python3 validate.py master  # first validate by the master rules

cd ..

rm -rf tmp-nomic-master

python3 validate.py proposed  # now validate by the new proposed rules
