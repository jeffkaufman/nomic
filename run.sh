#!/bin/bash
#
# Runs validate.py, setting things up the way Travis does.  Allows you to see
# the effects of changes.
#
# Usage:
#
#   ./run.sh [pr number] [commit sha]
#
# For example:
#
#   ./run.sh
#     Runs the "check if someone has won" version.
#
#   ./run.sh 33
#     Runs the "check if mergable" version on #33 at its HEAD
#
#   ./run.sh 33 ad567cd49e1c450
#     Same, but as of commit ad567cd49e1c450
#

export TRAVIS_REPO_SLUG="jeffkaufman/nomic"
API_URL="https://www.jefftk.com/nomic-github/repos/$TRAVIS_REPO_SLUG"

if [ $# -eq 0 ]; then
  export TRAVIS_PULL_REQUEST="false"
else
  export TRAVIS_PULL_REQUEST="$1"

  if [ $# -gt 1 ]; then
    export TRAVIS_PULL_REQUEST_SHA="$2"
  else
    export TRAVIS_PULL_REQUEST_SHA=$(curl -sS "$API_URL/pulls/$TRAVIS_PULL_REQUEST" | python3 -c "import sys, json; print(json.load(sys.stdin)['head']['sha'])")
  fi
fi

echo "TRAVIS_REPO_SLUG='$TRAVIS_REPO_SLUG'"
echo "TRAVIS_PULL_REQUEST='$TRAVIS_PULL_REQUEST'"
echo "TRAVIS_PULL_REQUEST_SHA='$TRAVIS_PULL_REQUEST_SHA'"
echo
echo "validate.py:"
python3 validate.py master
